#include <PresentMonAPI.h>
#include <Windows.h>
#include <SetupAPI.h>
#include <devguid.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace {
struct MetricSpec {
    PM_METRIC id;
    const char* csv;
    const char* symbol;
    const char* unit;
    bool system;
};

const std::vector<MetricSpec> specs = {
    {PM_METRIC_GPU_CARD_POWER, "gpu_card_power_w", "PM_METRIC_GPU_CARD_POWER", "W", false},
    {PM_METRIC_GPU_POWER, "gpu_power_w", "PM_METRIC_GPU_POWER", "W", false},
    {PM_METRIC_GPU_FREQUENCY, "gpu_frequency_mhz", "PM_METRIC_GPU_FREQUENCY", "MHz", false},
    {PM_METRIC_GPU_EFFECTIVE_FREQUENCY, "gpu_effective_frequency_mhz", "PM_METRIC_GPU_EFFECTIVE_FREQUENCY", "MHz", false},
    {PM_METRIC_GPU_UTILIZATION, "gpu_utilization_pct", "PM_METRIC_GPU_UTILIZATION", "%", false},
    {PM_METRIC_GPU_RENDER_COMPUTE_UTILIZATION, "gpu_compute_utilization_pct", "PM_METRIC_GPU_RENDER_COMPUTE_UTILIZATION", "%", false},
    {PM_METRIC_GPU_MEM_USED, "gpu_memory_used_mb", "PM_METRIC_GPU_MEM_USED", "MB", false},
    {PM_METRIC_GPU_MEM_FREQUENCY, "gpu_memory_frequency_mhz", "PM_METRIC_GPU_MEM_FREQUENCY", "MHz", false},
    {PM_METRIC_GPU_MEM_EFFECTIVE_FREQUENCY, "gpu_memory_effective_frequency_mhz", "PM_METRIC_GPU_MEM_EFFECTIVE_FREQUENCY", "MHz", false},
    {PM_METRIC_GPU_TEMPERATURE, "gpu_temperature_c", "PM_METRIC_GPU_TEMPERATURE", "C", false},
    {PM_METRIC_GPU_POWER_PERCENT, "gpu_power_percent", "PM_METRIC_GPU_POWER_PERCENT", "%", false},
    {PM_METRIC_CPU_POWER, "cpu_power_w", "PM_METRIC_CPU_POWER", "W", true},
};

void check(PM_STATUS status, const char* operation) {
    if (status != PM_STATUS_SUCCESS) {
        throw std::runtime_error(std::string(operation) + " failed, PM_STATUS=" + std::to_string((int)status));
    }
}

std::string jsonEscape(const std::string& s) {
    std::ostringstream out;
    for (unsigned char c : s) {
        if (c == '\\' || c == '"') out << '\\' << c;
        else if (c == '\n') out << "\\n";
        else if (c == '\r') out << "\\r";
        else if (c == '\t') out << "\\t";
        else if (c < 0x20) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << (int)c;
        else out << c;
    }
    return out.str();
}

std::string utcNow() {
    SYSTEMTIME t{}; GetSystemTime(&t);
    char b[64]{};
    std::snprintf(b, sizeof(b), "%04u-%02u-%02uT%02u:%02u:%02u.%03uZ",
        t.wYear, t.wMonth, t.wDay, t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
    return b;
}

bool supportsStat(const PM_INTROSPECTION_METRIC* metric, PM_STAT wanted) {
    if (!metric->pStatInfo) return false;
    for (size_t i = 0; i < metric->pStatInfo->size; ++i) {
        auto p = reinterpret_cast<const PM_INTROSPECTION_STAT_INFO*>(metric->pStatInfo->pData[i]);
        if (p && p->stat == wanted) return true;
    }
    return false;
}

const PM_INTROSPECTION_METRIC* findMetric(const PM_INTROSPECTION_ROOT* root, PM_METRIC id) {
    for (size_t i = 0; i < root->pMetrics->size; ++i) {
        auto p = reinterpret_cast<const PM_INTROSPECTION_METRIC*>(root->pMetrics->pData[i]);
        if (p && p->id == id) return p;
    }
    return nullptr;
}

bool availableOn(const PM_INTROSPECTION_METRIC* metric, uint32_t deviceId) {
    if (!metric || !metric->pDeviceMetricInfo) return false;
    for (size_t i = 0; i < metric->pDeviceMetricInfo->size; ++i) {
        auto p = reinterpret_cast<const PM_INTROSPECTION_DEVICE_METRIC_INFO*>(metric->pDeviceMetricInfo->pData[i]);
        if (p && p->deviceId == deviceId && p->availability == PM_METRIC_AVAILABILITY_AVAILABLE && p->arraySize > 0) return true;
    }
    return false;
}

struct Session {
    PM_SESSION_HANDLE h{};
    Session() { check(pmOpenSession(&h), "pmOpenSession"); }
    ~Session() { if (h) pmCloseSession(h); }
};
struct Intro {
    const PM_INTROSPECTION_ROOT* p{};
    PM_SESSION_HANDLE h{};
    explicit Intro(PM_SESSION_HANDLE session) : h(session) { check(pmGetIntrospectionRoot(h, &p), "pmGetIntrospectionRoot"); }
    ~Intro() { if (p) pmFreeIntrospectionRoot(p); }
};
struct Query {
    PM_DYNAMIC_QUERY_HANDLE h{};
    ~Query() { if (h) pmFreeDynamicQuery(h); }
};

struct WindowsGpuIdentity {
    std::string driverVersion;
    std::string pnpDeviceId;
};

WindowsGpuIdentity findWindowsGpuIdentity() {
    WindowsGpuIdentity found;
    HDEVINFO devices = SetupDiGetClassDevsA(&GUID_DEVCLASS_DISPLAY, nullptr, nullptr, DIGCF_PRESENT);
    if (devices == INVALID_HANDLE_VALUE) return found;
    for (DWORD index = 0;; ++index) {
        SP_DEVINFO_DATA data{}; data.cbSize = sizeof(data);
        if (!SetupDiEnumDeviceInfo(devices, index, &data)) break;
        char description[512]{}; DWORD type = 0, needed = 0;
        if (!SetupDiGetDeviceRegistryPropertyA(devices, &data, SPDRP_DEVICEDESC, &type,
                reinterpret_cast<PBYTE>(description), sizeof(description), &needed)) continue;
        if (std::string(description).find("B570") == std::string::npos) continue;
        char instance[1024]{};
        if (SetupDiGetDeviceInstanceIdA(devices, &data, instance, sizeof(instance), &needed)) found.pnpDeviceId = instance;
        char driverKey[512]{};
        if (SetupDiGetDeviceRegistryPropertyA(devices, &data, SPDRP_DRIVER, &type,
                reinterpret_cast<PBYTE>(driverKey), sizeof(driverKey), &needed)) {
            const std::string path = "SYSTEM\\CurrentControlSet\\Control\\Class\\" + std::string(driverKey);
            HKEY key{};
            if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, path.c_str(), 0, KEY_READ, &key) == ERROR_SUCCESS) {
                char value[256]{}; DWORD bytes = sizeof(value);
                if (RegQueryValueExA(key, "DriverVersion", nullptr, &type, reinterpret_cast<PBYTE>(value), &bytes) == ERROR_SUCCESS) found.driverVersion = value;
                RegCloseKey(key);
            }
        }
        break;
    }
    SetupDiDestroyDeviceInfoList(devices);
    return found;
}
}

int main(int argc, char** argv) try {
    if (argc != 5 && argc != 6) {
        std::cerr << "usage: b570_presentmon_telemetry <csv> <metadata.json> <max_duration_s> <period_ms> [stop_file]\n";
        return 2;
    }
    const std::string csvPath = argv[1], metadataPath = argv[2];
    const double duration = std::stod(argv[3]);
    const uint32_t periodMs = (uint32_t)std::stoul(argv[4]);
    const double queryWindowMs = 1000.0;
    const std::optional<std::filesystem::path> stopFile = argc == 6 ? std::optional<std::filesystem::path>(argv[5]) : std::nullopt;
    if (periodMs < 50 || periodMs > 5000 || duration <= 0) throw std::runtime_error("invalid duration/period");

    LARGE_INTEGER qpf{}; QueryPerformanceFrequency(&qpf);
    PM_VERSION api{}; check(pmGetApiVersion(&api), "pmGetApiVersion");
    Session session;
    Intro intro(session.h);

    uint32_t gpuId = 0, systemId = 0;
    std::string gpuName;
    for (size_t i = 0; i < intro.p->pDevices->size; ++i) {
        auto d = reinterpret_cast<const PM_INTROSPECTION_DEVICE*>(intro.p->pDevices->pData[i]);
        if (!d || !d->pName || !d->pName->pData) continue;
        std::string name = d->pName->pData;
        if (d->type == PM_DEVICE_TYPE_GRAPHICS_ADAPTER && name.find("B570") != std::string::npos) { gpuId = d->id; gpuName = name; }
        if (d->type == PM_DEVICE_TYPE_SYSTEM) systemId = d->id;
    }
    if (!gpuId) throw std::runtime_error("Arc B570 not found in PresentMon introspection");
    const auto windowsGpu = findWindowsGpuIdentity();
    check(pmSetTelemetryPollingPeriod(session.h, gpuId, periodMs), "pmSetTelemetryPollingPeriod(B570)");
    if (systemId) check(pmSetTelemetryPollingPeriod(session.h, systemId, periodMs), "pmSetTelemetryPollingPeriod(system)");

    std::vector<PM_QUERY_ELEMENT> elements;
    std::vector<const MetricSpec*> queried;
    std::map<std::string, bool> availability;
    for (const auto& spec : specs) {
        const auto metric = findMetric(intro.p, spec.id);
        const uint32_t device = spec.system ? systemId : gpuId;
        const PM_STAT stat = spec.id == PM_METRIC_GPU_CARD_POWER ? PM_STAT_NEWEST_POINT : PM_STAT_AVG;
        bool ok = device && availableOn(metric, device) && supportsStat(metric, stat);
        availability[spec.symbol] = ok;
        if (ok) {
            elements.push_back(PM_QUERY_ELEMENT{spec.id, stat, device, 0, 0, 0});
            queried.push_back(&spec);
        }
    }
    if (!availability["PM_METRIC_GPU_CARD_POWER"]) throw std::runtime_error("PM_METRIC_GPU_CARD_POWER unavailable on Arc B570");
    const auto cpuUtilMetric = findMetric(intro.p, PM_METRIC_CPU_UTILIZATION);
    const auto cpuFreqMetric = findMetric(intro.p, PM_METRIC_CPU_FREQUENCY);
    const bool cpuUtilAvailable = systemId && availableOn(cpuUtilMetric, systemId) && supportsStat(cpuUtilMetric, PM_STAT_AVG);
    const bool cpuFreqAvailable = systemId && availableOn(cpuFreqMetric, systemId) && supportsStat(cpuFreqMetric, PM_STAT_AVG);

    Query query;
    check(pmRegisterDynamicQuery(session.h, &query.h, elements.data(), elements.size(), queryWindowMs, 0.0), "pmRegisterDynamicQuery");
    uint64_t blobSize = 0;
    for (const auto& e : elements) blobSize = (std::max)(blobSize, e.dataOffset + e.dataSize);
    std::vector<uint8_t> blob((size_t)blobSize);

    std::ofstream csv(csvPath, std::ios::binary);
    if (!csv) throw std::runtime_error("cannot open CSV");
    csv << "timestamp_utc,qpc_timestamp,sample_index,adapter_name,adapter_id";
    for (const auto& spec : specs) csv << ',' << spec.csv;
    csv << "\n";

    const auto startUtc = utcNow();
    LARGE_INTEGER startQpc{}; QueryPerformanceCounter(&startQpc);
    auto next = std::chrono::steady_clock::now();
    const auto deadline = next + std::chrono::duration<double>(duration);
    uint64_t index = 0;
    while (std::chrono::steady_clock::now() < deadline && !(stopFile && std::filesystem::exists(*stopFile))) {
        uint32_t count = 1;
        check(pmPollDynamicQuery(query.h, 0, blob.data(), &count), "pmPollDynamicQuery(PID=0)");
        LARGE_INTEGER qpc{}; QueryPerformanceCounter(&qpc);
        std::map<PM_METRIC, double> values;
        for (size_t i = 0; i < elements.size(); ++i) {
            double v = *reinterpret_cast<const double*>(blob.data() + elements[i].dataOffset);
            if (std::isfinite(v)) values[elements[i].metric] = v;
        }
        csv << utcNow() << ',' << qpc.QuadPart << ',' << index++ << ",\"" << gpuName << "\"," << gpuId;
        for (const auto& spec : specs) {
            auto it = values.find(spec.id);
            if (it != values.end()) {
                double value = it->second;
                if (spec.id == PM_METRIC_GPU_MEM_USED) value /= 1024.0 * 1024.0;
                csv << ',' << std::setprecision(12) << value;
            }
            else csv << ',';
        }
        csv << "\n"; csv.flush();
        next += std::chrono::milliseconds(periodMs);
        std::this_thread::sleep_until(next);
    }
    LARGE_INTEGER endQpc{}; QueryPerformanceCounter(&endQpc);
    const auto endUtc = utcNow();

    std::ofstream meta(metadataPath, std::ios::binary);
    meta << "{\n  \"schema\": \"heterospec.presentmon_telemetry.v1\",\n"
         << "  \"presentmon_api_version\": \"" << api.major << '.' << api.minor << '.' << api.patch << "\",\n"
         << "  \"adapter_name\": \"" << jsonEscape(gpuName) << "\",\n"
         << "  \"adapter_id\": " << gpuId << ",\n"
         << "  \"gpu_driver_version\": \"" << jsonEscape(windowsGpu.driverVersion) << "\",\n"
         << "  \"pnp_device_id\": \"" << jsonEscape(windowsGpu.pnpDeviceId) << "\",\n"
         << "  \"polling_period_ms\": " << periodMs << ",\n"
         << "  \"query_window_ms\": " << queryWindowMs << ",\n"
         << "  \"gpu_card_power_stat\": \"PM_STAT_NEWEST_POINT\",\n"
         << "  \"pid\": 0,\n  \"presenter_required\": false,\n"
         << "  \"qpc_frequency\": " << qpf.QuadPart << ",\n"
         << "  \"start_utc\": \"" << startUtc << "\",\n  \"end_utc\": \"" << endUtc << "\",\n"
         << "  \"start_qpc\": " << startQpc.QuadPart << ",\n  \"end_qpc\": " << endQpc.QuadPart << ",\n"
         << "  \"samples\": " << index << ",\n  \"metrics\": {\n";
    for (size_t i = 0; i < specs.size(); ++i) {
        const auto& s = specs[i];
        meta << "    \"" << s.symbol << "\": {\"supported\": " << (availability[s.symbol] ? "true" : "false")
             << ", \"unit\": \"" << s.unit << "\"},\n";
    }
    meta << "    \"PM_METRIC_CPU_FREQUENCY\": {\"supported\": " << (cpuFreqAvailable ? "true" : "false") << ", \"unit\": \"MHz\", \"queried\": false},\n"
         << "    \"PM_METRIC_CPU_UTILIZATION\": {\"supported\": " << (cpuUtilAvailable ? "true" : "false") << ", \"unit\": \"%\", \"queried\": false}\n";
    meta << "  }\n}\n";
    std::cout << "samples=" << index << " adapter=\"" << gpuName << "\" card_power=SUPPORTED\n";
    return 0;
} catch (const std::exception& e) {
    std::cerr << "collector error: " << e.what() << '\n';
    return 1;
}
