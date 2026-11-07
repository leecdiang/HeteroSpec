#include <level_zero/zes_api.h>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

static const char* freqName(zes_freq_domain_t t) {
    return t == ZES_FREQ_DOMAIN_GPU ? "GPU" : t == ZES_FREQ_DOMAIN_MEMORY ? "MEMORY" : "OTHER";
}

int main(int argc, char** argv) {
    int waitMs = argc > 1 ? std::stoi(argv[1]) : 1000;
    ze_result_t init = zesInit(0);
    std::cout << "{\n  \"zes_init_result\": " << (uint32_t)init;
    if (init != ZE_RESULT_SUCCESS) { std::cout << ",\n  \"devices\": []\n}\n"; return 1; }
    uint32_t driverCount = 0;
    ze_result_t dr = zesDriverGet(&driverCount, nullptr);
    std::vector<zes_driver_handle_t> drivers(driverCount);
    if (dr == ZE_RESULT_SUCCESS) dr = zesDriverGet(&driverCount, drivers.data());
    std::cout << ",\n  \"driver_get_result\": " << (uint32_t)dr << ",\n  \"devices\": [\n";
    bool firstDevice = true;
    for (auto driver : drivers) {
        uint32_t deviceCount = 0;
        if (zesDeviceGet(driver, &deviceCount, nullptr) != ZE_RESULT_SUCCESS) continue;
        std::vector<zes_device_handle_t> devices(deviceCount);
        if (zesDeviceGet(driver, &deviceCount, devices.data()) != ZE_RESULT_SUCCESS) continue;
        for (auto device : devices) {
            zes_device_properties_t dp{}; dp.stype = ZES_STRUCTURE_TYPE_DEVICE_PROPERTIES;
            auto propResult = zesDeviceGetProperties(device, &dp);
            if (!firstDevice) std::cout << ",\n";
            firstDevice = false;
            const char* model = dp.modelName[0] ? dp.modelName : dp.core.name;
            std::cout << "    {\"model\": \"" << (propResult == ZE_RESULT_SUCCESS ? model : "UNKNOWN")
                      << "\", \"vendor_id\": " << dp.core.vendorId << ", \"device_id\": " << dp.core.deviceId
                      << ", \"driver_version\": \"" << dp.driverVersion << "\", \"power_domains\": [";
            uint32_t powerCount = 0; zesDeviceEnumPowerDomains(device, &powerCount, nullptr);
            std::vector<zes_pwr_handle_t> powers(powerCount); if (powerCount) zesDeviceEnumPowerDomains(device, &powerCount, powers.data());
            for (uint32_t i = 0; i < powerCount; ++i) {
                if (i) std::cout << ',';
                zes_power_properties_t pp{}; pp.stype = ZES_STRUCTURE_TYPE_POWER_PROPERTIES;
                auto ppr = zesPowerGetProperties(powers[i], &pp);
                zes_power_energy_counter_t e0{}, e1{};
                auto e0r = zesPowerGetEnergyCounter(powers[i], &e0);
                uint32_t instant = 0, average = 0; auto ur = zesPowerGetUsage(powers[i], &instant, &average);
                std::this_thread::sleep_for(std::chrono::milliseconds(waitMs));
                auto e1r = zesPowerGetEnergyCounter(powers[i], &e1);
                std::cout << "{\"index\":" << i << ",\"properties_result\":" << (uint32_t)ppr
                          << ",\"on_subdevice\":" << (pp.onSubdevice ? "true" : "false") << ",\"subdevice_id\":" << pp.subdeviceId
                          << ",\"energy_result\":" << (uint32_t)(e0r == ZE_RESULT_SUCCESS ? e1r : e0r)
                          << ",\"energy_start_uj\":" << e0.energy << ",\"energy_end_uj\":" << e1.energy
                          << ",\"timestamp_start_us\":" << e0.timestamp << ",\"timestamp_end_us\":" << e1.timestamp
                          << ",\"usage_result\":" << (uint32_t)ur << ",\"instant_power_mw\":" << instant << ",\"average_power_mw\":" << average << '}';
            }
            std::cout << "], \"frequency_domains\": [";
            uint32_t freqCount = 0; zesDeviceEnumFrequencyDomains(device, &freqCount, nullptr);
            std::vector<zes_freq_handle_t> freqs(freqCount); if (freqCount) zesDeviceEnumFrequencyDomains(device, &freqCount, freqs.data());
            for (uint32_t i = 0; i < freqCount; ++i) {
                if (i) std::cout << ',';
                zes_freq_properties_t fp{}; fp.stype = ZES_STRUCTURE_TYPE_FREQ_PROPERTIES;
                zes_freq_state_t fs{}; fs.stype = ZES_STRUCTURE_TYPE_FREQ_STATE;
                auto fpr = zesFrequencyGetProperties(freqs[i], &fp); auto fsr = zesFrequencyGetState(freqs[i], &fs);
                std::cout << "{\"index\":" << i << ",\"type\":\"" << freqName(fp.type) << "\",\"properties_result\":" << (uint32_t)fpr
                          << ",\"state_result\":" << (uint32_t)fsr << ",\"actual_mhz\":" << fs.actual << ",\"requested_mhz\":" << fs.request << '}';
            }
            std::cout << "]}";
        }
    }
    std::cout << "\n  ]\n}\n";
    return 0;
}
