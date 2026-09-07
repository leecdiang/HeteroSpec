#include <errno.h>
#include <inttypes.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "ThermalBenchTelemetry.h"

static volatile sig_atomic_t stop_requested = 0;

static void request_stop(int signal_number) {
    (void)signal_number;
    stop_requested = 1;
}

static unsigned parse_positive(const char *text, const char *name) {
    char *end = NULL;
    errno = 0;
    unsigned long value = strtoul(text, &end, 10);
    if (errno || !end || *end || value == 0 || value > 3600000UL) {
        fprintf(stderr, "invalid %s: %s\n", name, text);
        exit(64);
    }
    return (unsigned)value;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s INTERVAL_MS SAMPLE_COUNT\n", argv[0]);
        return 64;
    }
    unsigned interval_ms = parse_positive(argv[1], "interval");
    unsigned sample_count = parse_positive(argv[2], "sample count");
    signal(SIGINT, request_stop);
    signal(SIGTERM, request_stop);

    TBTelemetryHandle handle = tb_telemetry_create();
    if (!handle) {
        fprintf(stderr, "Silemetry create failed\n");
        return 1;
    }
    TBErrorCode rc = tb_telemetry_start(handle, interval_ms);
    if (rc != TB_OK) {
        fprintf(stderr, "Silemetry start failed: %d\n", rc);
        tb_telemetry_destroy(handle);
        return 2;
    }

    puts("sequence,wall_clock_unix_ns,available_mask,cpu_temp_avg_c,cpu_temp_hottest_c,gpu_temp_avg_c,gpu_temp_hottest_c,cpu_sensor_count,gpu_sensor_count,cpu_power_w,gpu_power_w,ane_power_w,dram_power_w,package_power_w,p_freq_mhz,e_freq_mhz,p_util,e_util,cpu_util,gpu_util");
    fflush(stdout);

    uint64_t sequence = 0;
    unsigned startup_waits = 0;
    unsigned emitted = 0;
    while (emitted < sample_count && !stop_requested) {
        TBTelemetrySample sample = {0};
        rc = tb_telemetry_wait_next(handle, sequence, interval_ms * 3, &sample);
        if (rc == TB_ERR_NOT_STARTED && startup_waits++ < 100) {
            usleep(100000);
            continue;
        }
        if (rc != TB_OK) {
            char error[512] = {0};
            tb_telemetry_last_error(handle, error, sizeof(error));
            fprintf(stderr, "Silemetry sample failed: %d %s\n", rc, error);
            break;
        }
        sequence = sample.sequence_id;
        printf("%" PRIu64 ",%" PRId64 ",0x%llx,%.3f,%.3f,%.3f,%.3f,%u,%u,%.6f,%.6f,%.6f,%.6f,%.6f,%.3f,%.3f,%.6f,%.6f,%.6f,%.6f\n",
               sample.sequence_id,
               sample.wall_clock_unix_ns,
               (unsigned long long)sample.available_mask,
               sample.cpu_temperature_avg_c,
               sample.cpu_temperature_hottest_c,
               sample.gpu_temperature_avg_c,
               sample.gpu_temperature_hottest_c,
               sample.cpu_temperature_sensor_count,
               sample.gpu_temperature_sensor_count,
               sample.cpu_power_w,
               sample.gpu_power_w,
               sample.ane_power_w,
               sample.dram_power_w,
               sample.package_power_w,
               sample.p_cluster_frequency_mhz,
               sample.e_cluster_frequency_mhz,
               sample.p_cluster_utilization_ratio,
               sample.e_cluster_utilization_ratio,
               sample.cpu_utilization_ratio,
               sample.gpu_utilization_ratio);
        fflush(stdout);
        ++emitted;
    }

    tb_telemetry_stop(handle);
    tb_telemetry_destroy(handle);
    return (emitted == sample_count || stop_requested) ? 0 : 3;
}
