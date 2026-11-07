#pragma once
// Host integration template; MUST execute inside the resident model worker PID.
// Reviewed against Vulkan specification, but compile/runtime validation is pending B570 SDK.
#include <vulkan/vulkan.h>
#include <cstdint>
#include <vector>
#include <cstring>
#include <stdexcept>

namespace b570_opt {
struct heap_sample {
    uint32_t index;
    uint64_t physical_size_bytes;
    uint64_t budget_bytes;
    uint64_t usage_bytes;
    bool device_local; // NOT automatically proof of dedicated heap/no shared spill.
};

inline std::vector<heap_sample> owned_process_memory(VkPhysicalDevice device) {
    uint32_t count = 0;
    if (vkEnumerateDeviceExtensionProperties(device, nullptr, &count, nullptr) != VK_SUCCESS)
        throw std::runtime_error("Cannot enumerate Vulkan device extensions");
    std::vector<VkExtensionProperties> extensions(count);
    if (vkEnumerateDeviceExtensionProperties(device, nullptr, &count, extensions.data()) != VK_SUCCESS)
        throw std::runtime_error("Vulkan extension enumeration failed");
    bool supported = false;
    for (const auto & x : extensions)
        if (std::strcmp(x.extensionName, VK_EXT_MEMORY_BUDGET_EXTENSION_NAME) == 0) supported = true;
    if (!supported) throw std::runtime_error("VK_EXT_memory_budget unavailable; no residency claim");
    // Instance must expose Vulkan 1.1+ vkGetPhysicalDeviceMemoryProperties2.
    VkPhysicalDeviceMemoryBudgetPropertiesEXT budget{};
    budget.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_BUDGET_PROPERTIES_EXT;
    VkPhysicalDeviceMemoryProperties2 memory{};
    memory.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_PROPERTIES_2;
    memory.pNext = &budget;
    vkGetPhysicalDeviceMemoryProperties2(device, &memory);
    std::vector<heap_sample> result;
    for (uint32_t i = 0; i < memory.memoryProperties.memoryHeapCount; ++i) {
        const auto & h = memory.memoryProperties.memoryHeaps[i];
        result.push_back({i, h.size, budget.heapBudget[i], budget.heapUsage[i],
                          (h.flags & VK_MEMORY_HEAP_DEVICE_LOCAL_BIT) != 0});
    }
    return result;
}
} // namespace b570_opt
