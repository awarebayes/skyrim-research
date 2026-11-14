// Build: sse-steam-1-7-104
// Labels: v2
// Source exposure: mixed (community headers and pinned-image analysis).
// Drafted by gpt-6.1-sol, Engineer p105 box3. Adapted bodies: none.
// Declarations adapt CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a (MIT).
// Helper spellings and local variable names are inferred; individual labels accompany declarations.
// MIT License
// 
// Copyright (c) 2018 Ryan-rsm-McKenzie
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
// BSComputeShader: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
#pragma once
#include <cstdint>
#include <cstddef>
#include <intrin.h>
// The object counter is decremented atomically at the end of its base lifetime.
class NiRefObject { public: virtual ~NiRefObject() { _InterlockedDecrement(&ms_totalObjects); } virtual void DeleteThis(); static volatile long ms_totalObjects; std::uint32_t refCount; };
struct ShaderEntry { std::uint32_t key; void* value; ShaderEntry* next; };
struct ShaderTableTail { ~ShaderTableTail(); std::uint32_t unknown00,capacity,freeCount,good; ShaderEntry* sentinel; std::uint64_t allocatorState; ShaderEntry* entries; };
class BSReloadShaderI { public: virtual void ReloadShaders(void*)=0; };
class BSComputeShader : public NiRefObject, public BSReloadShaderI { public: BSComputeShader(); ~BSComputeShader() override; void ReloadShaders(void*) override; virtual void Dispatch(std::uint32_t,std::uint32_t,std::uint32_t,std::uint32_t); const char* name; std::uint64_t tableUnknown00; ShaderTableTail table; };
static_assert(sizeof(BSComputeShader)==0x50,"compute shader size");
void ReleaseShaderName(const char*); extern std::uint64_t Renderer; extern const char ShaderErrorFormat[];
void BindComputeShader(void*,void*,std::uint32_t,std::uint32_t,std::uint32_t); int ShaderFormat(char*,std::size_t,const char*,...);
extern "C" __declspec(dllimport) void __stdcall OutputDebugStringA(const char*);

