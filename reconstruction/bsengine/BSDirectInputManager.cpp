// BSDirectInputManager methods, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0xcfaeb0, 37 bytes: ReleaseDevice
// RVA 0xcfae70, 48 bytes: CreateDeviceWithGUID
// RVA 0xcfaee0, 113 bytes: GetDeviceState
// RVA 0xcfaf60, 126 bytes: GetDeviceData
//
// Evidence: findings/third-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with types from the header beside this file.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. All four functions are compared.
#include "BSDirectInputManager.h"

#include <cstring>

void BSDirectInputManager::ReleaseDevice(IDirectInputDevice8A* a_device)
{
    if (a_device) {
        a_device->Unacquire();
        a_device->Release();
    }
}

IDirectInputDevice8A* BSDirectInputManager::CreateDeviceWithGUID(GUID* a_guid)
{
    IDirectInputDevice8A* device;
    if (diInterface && diInterface->CreateDevice(a_guid, &device, nullptr) == 0) {
        return device;
    }
    return nullptr;
}

void BSDirectInputManager::GetDeviceState(IDirectInputDevice8A* a_device, std::uint32_t a_size,
                                          void* a_outData)
{
    if (!a_device) {
        return;
    }
    // Acquire returns S_OK or S_FALSE when the device is held; anything else yields a zeroed state.
    if (static_cast<std::uint32_t>(a_device->Acquire()) > 1) {
        std::memset(a_outData, 0, a_size);
        return;
    }
    a_device->Poll();
    a_device->GetDeviceState(a_size, a_outData);
}

void BSDirectInputManager::GetDeviceData(IDirectInputDevice8A* a_device, std::uint32_t* a_dataSize,
                                         DIDEVICEOBJECTDATA** a_outData)
{
    if (!a_device) {
        return;
    }
    if (static_cast<std::uint32_t>(a_device->Acquire()) > 1) {
        if (a_dataSize) {
            *a_dataSize = 0;
        }
        return;
    }
    a_device->Poll();
    a_device->GetDeviceData(sizeof(DIDEVICEOBJECTDATA), a_outData, a_dataSize, 0);
}
