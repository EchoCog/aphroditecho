/*
 * DTESN Performance Profile Analyzer
 * ==================================
 * 
 * Standalone tool for analyzing DTESN performance profiling data
 * and generating comprehensive performance reports.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <getopt.h>
#include <time.h>
#include <errno.h>
#include "../../include/dtesn/profiler.h"

/* Command line options */
static struct option long_options[] = {
    {"help",        no_argument,       0, 'h'},
    {"version",     no_argument,       0, 'v'},
    {"output",      required_argument, 0, 'o'},
    {"format",      required_argument, 0, 'f'},
    {"threshold",   required_argument, 0, 't'},
    {"reset",       no_argument,       0, 'r'},
    {"overhead",    no_argument,       0, 'O'},
    {"continuous",  required_argument, 0, 'c'},
    {0, 0, 0, 0}
};

/* Output formats */
typedef enum {
    FORMAT_TEXT = 0,
    FORMAT_JSON,
    FORMAT_CSV
} output_format_t;

/* Configuration */
typedef struct {
    char *output_file;
    output_format_t format;
    double threshold_ms;
    bool reset_stats;
    bool measure_overhead;
    int continuous_seconds;
} analyzer_config_t;

/**
 * print_usage - Display usage information
 */
static void print_usage(const char *program_name)
{
    printf("DTESN Performance Profile Analyzer\n");
    printf("Usage: %s [OPTIONS]\n\n", program_name);
    printf("Options:\n");
    printf("  -h, --help              Show this help message\n");
    printf("  -v, --version           Show version information\n");
    printf("  -o, --output FILE       Output file (default: stdout)\n");
    printf("  -f, --format FORMAT     Output format: text, json, csv (default: text)\n");
    printf("  -t, --threshold MS      Performance violation threshold in ms (default: 1.0)\n");
    printf("  -r, --reset             Reset profiling statistics before analysis\n");
    printf("  -O, --overhead          Measure and report profiling overhead\n");
    printf("  -c, --continuous SEC    Continuous monitoring for SEC seconds\n\n");
    printf("Examples:\n");
    printf("  %s                      # Generate basic performance report\n", program_name);
    printf("  %s -f json -o report.json  # Generate JSON report to file\n", program_name);
    printf("  %s -c 30 -t 0.5         # Monitor for 30 seconds with 0.5ms threshold\n", program_name);
}

/**
 * print_version - Display version information
 */
static void print_version(void)
{
    printf("DTESN Performance Profile Analyzer v1.0\n");
    printf("Deep Tree Echo State Networks Kernel Performance Tool\n");
    printf("Copyright (C) 2024 Echo.Kern Project\n");
}

/**
 * parse_format - Parse output format string
 */
static output_format_t parse_format(const char *format_str)
{
    if (strcmp(format_str, "json") == 0) {
        return FORMAT_JSON;
    } else if (strcmp(format_str, "csv") == 0) {
        return FORMAT_CSV;
    } else {
        return FORMAT_TEXT;
    }
}

/**
 * generate_json_report - Generate JSON format report
 */
static int generate_json_report(FILE *output, const char *report_data)
{
    time_t current_time = time(NULL);
    struct tm *time_info = localtime(&current_time);
    char timestamp[64];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", time_info);
    
    fprintf(output, "{\n");
    fprintf(output, "  \"dtesn_profiling_report\": {\n");
    fprintf(output, "    \"timestamp\": \"%s\",\n", timestamp);
    fprintf(output, "    \"version\": \"1.0\",\n");
    fprintf(output, "    \"data\": \"%s\"\n", report_data);
    fprintf(output, "  }\n");
    fprintf(output, "}\n");
    
    return 0;
}

/**
 * generate_csv_header - Generate CSV format header
 */
static int generate_csv_header(FILE *output)
{
    fprintf(output, "operation,count,total_time_ns,avg_time_ns,min_time_ns,max_time_ns,violations,target_ns\n");
    return 0;
}

/**
 * measure_overhead - Measure profiling system overhead
 */
static int measure_overhead(FILE *output)
{
    fprintf(output, "Measuring DTESN profiling overhead...\n");
    
    /* Initialize profiler if not already done */
    int ret = dtesn_profile_init(0);
    if (ret != 0 && ret != -EALREADY) {
        fprintf(stderr, "Failed to initialize profiler: %d\n", ret);
        return ret;
    }
    
    /* Measure overhead */
    uint64_t overhead_ns = dtesn_profile_overhead();
    double overhead_ms = overhead_ns / 1000000.0;
    double overhead_percent = (overhead_ns / 1000.0) * 0.1; /* Rough estimate */
    
    fprintf(output, "\nProfiling Overhead Analysis:\n");
    fprintf(output, "============================\n");
    fprintf(output, "Measured overhead: %lu ns (%.3f ms)\n", overhead_ns, overhead_ms);
    fprintf(output, "Estimated impact: %.2f%%\n", overhead_percent);
    fprintf(output, "Target threshold: ≤ 2.0%%\n");
    
    if (overhead_percent <= 2.0) {
        fprintf(output, "Status: ✅ WITHIN TARGET\n");
    } else {
        fprintf(output, "Status: ❌ EXCEEDS TARGET\n");
    }
    
    return 0;
}

/**
 * continuous_monitoring - Perform continuous performance monitoring
 */
static int continuous_monitoring(int duration_seconds, double threshold_ms, FILE *output)
{
    fprintf(output, "Starting continuous monitoring for %d seconds...\n", duration_seconds);
    fprintf(output, "Performance threshold: %.2f ms\n\n", threshold_ms);
    
    /* Initialize profiler */
    int ret = dtesn_profile_init(0);
    if (ret != 0 && ret != -EALREADY) {
        fprintf(stderr, "Failed to initialize profiler: %d\n", ret);
        return ret;
    }
    
    /* Reset statistics */
    dtesn_profile_reset();
    
    time_t start_time = time(NULL);
    time_t end_time = start_time + duration_seconds;
    
    while (time(NULL) < end_time) {
        /* Generate intermediate report */
        char report_buffer[8192];
        ret = dtesn_profile_report(report_buffer, sizeof(report_buffer));
        if (ret > 0) {
            fprintf(output, "--- Report at %ld seconds ---\n", time(NULL) - start_time);
            fprintf(output, "%s", report_buffer);
            fprintf(output, "\n");
        }
        
        /* Sleep for 1 second intervals */
        sleep(1);
    }
    
    fprintf(output, "Continuous monitoring completed.\n");
    return 0;
}

/**
 * main - Profile analyzer main function
 */
int main(int argc, char *argv[])
{
    analyzer_config_t config = {
        .output_file = NULL,
        .format = FORMAT_TEXT,
        .threshold_ms = 1.0,
        .reset_stats = false,
        .measure_overhead = false,
        .continuous_seconds = 0
    };
    
    /* Parse command line arguments */
    int c;
    while ((c = getopt_long(argc, argv, "hvo:f:t:rOc:", long_options, NULL)) != -1) {
        switch (c) {
        case 'h':
            print_usage(argv[0]);
            return 0;
        case 'v':
            print_version();
            return 0;
        case 'o':
            config.output_file = optarg;
            break;
        case 'f':
            config.format = parse_format(optarg);
            break;
        case 't':
            config.threshold_ms = atof(optarg);
            break;
        case 'r':
            config.reset_stats = true;
            break;
        case 'O':
            config.measure_overhead = true;
            break;
        case 'c':
            config.continuous_seconds = atoi(optarg);
            break;
        default:
            print_usage(argv[0]);
            return 1;
        }
    }
    
    /* Open output file or use stdout */
    FILE *output = stdout;
    if (config.output_file) {
        output = fopen(config.output_file, "w");
        if (!output) {
            perror("Failed to open output file");
            return 1;
        }
    }
    
    /* Initialize profiler */
    int ret = dtesn_profile_init(0);
    if (ret != 0 && ret != -EALREADY) {
        fprintf(stderr, "Failed to initialize profiler: %d\n", ret);
        if (output != stdout) fclose(output);
        return 1;
    }
    
    /* Reset statistics if requested */
    if (config.reset_stats) {
        dtesn_profile_reset();
        fprintf(output, "Profiling statistics reset.\n\n");
    }
    
    /* Handle special modes */
    if (config.measure_overhead) {
        ret = measure_overhead(output);
        if (output != stdout) fclose(output);
        return ret;
    }
    
    if (config.continuous_seconds > 0) {
        ret = continuous_monitoring(config.continuous_seconds, config.threshold_ms, output);
        if (output != stdout) fclose(output);
        return ret;
    }
    
    /* Generate standard report */
    char report_buffer[8192];
    ret = dtesn_profile_report(report_buffer, sizeof(report_buffer));
    if (ret < 0) {
        fprintf(stderr, "Failed to generate report: %d\n", ret);
        if (output != stdout) fclose(output);
        return 1;
    }
    
    /* Output in requested format */
    switch (config.format) {
    case FORMAT_JSON:
        generate_json_report(output, report_buffer);
        break;
    case FORMAT_CSV:
        generate_csv_header(output);
        /* Note: CSV format would need parsing of the text report */
        fprintf(output, "# CSV format not fully implemented yet\n");
        fprintf(output, "# Raw data:\n%s", report_buffer);
        break;
    case FORMAT_TEXT:
    default:
        fprintf(output, "%s", report_buffer);
        break;
    }
    
    /* Cleanup */
    if (output != stdout) {
        fclose(output);
    }
    
    return 0;
}