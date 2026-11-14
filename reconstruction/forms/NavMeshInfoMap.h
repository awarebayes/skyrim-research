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
// NavMeshInfoMap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
#pragma once
#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"
inline BaseFormComponent::~BaseFormComponent() {}
// ArrayOwner, ClearArray, ResetArrayCount, ReleaseArray: GUESS(low); represented heap array ownership.
void ClearArray(void*); void ResetArrayCount(std::uint32_t*); void ReleaseArray(void*);
struct ArrayOwner {
 void** data; std::uint32_t capacity; std::uint32_t allocatorState; std::uint32_t count; std::uint32_t unknown14;
 ~ArrayOwner() { if(data) { ClearArray(this); count=0; } else ResetArrayCount(&count); ReleaseArray(this); }
};
static_assert(sizeof(ArrayOwner)==0x18,"heap array size");
struct NavEntry { std::uint64_t key; void* value; NavEntry* next; };
struct NavMapTail { ~NavMapTail(); std::uint32_t unknown00,capacity,freeCount,good; NavEntry* sentinel; std::uint64_t allocatorState; NavEntry* entries; };
struct CKMapTail { ~CKMapTail(); std::uint32_t unknown00,capacity,freeCount,good; NavEntry* sentinel; std::uint64_t allocatorState; NavEntry* entries; };
struct NavMap { std::uint64_t unknown00; NavMapTail tail; }; struct CKMap { std::uint64_t unknown00; CKMapTail tail; };
template<class T> struct BSTSingletonExplicit {};
struct PrecomputedPaths : public BSTSingletonExplicit<PrecomputedPaths> { ~PrecomputedPaths(); ArrayOwner allPaths; NavMap infoToIndexMap; };
class BSNavmeshInfoMap : public BSTSingletonExplicit<BSNavmeshInfoMap> { public: BSNavmeshInfoMap(); virtual ~BSNavmeshInfoMap(); };
class NavMeshInfoMap : public TESForm, public BSNavmeshInfoMap, public PrecomputedPaths { public: NavMeshInfoMap(); ~NavMeshInfoMap() override; virtual void SetAltered(bool); bool updateAll; NavMap infoMap; CKMap ckNavMeshInfoMap; std::uint32_t lockThread,lockState; bool init; }; static_assert(sizeof(NavMeshInfoMap)==0xF0,"navmesh map size");
void ClearNavMap(NavMeshInfoMap*); void BaseSetAltered(TESForm*,bool); void LockNavMap(void*); void UnlockNavMap(void*); void SetNavInfoAltered(void*,bool);


struct NavWriteScope { void* lock; explicit NavWriteScope(void* value):lock(value) { LockNavMap(lock); } ~NavWriteScope() { if(lock) UnlockNavMap(lock); } };
