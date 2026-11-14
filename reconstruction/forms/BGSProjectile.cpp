// Build: sse-steam-1-7-104
// Labels: v2
// Source exposure: mixed (community headers and pinned-image analysis).
// Code origin: original reconstruction; declarations adapted from the pinned MIT community headers.
// Drafted by gpt-6.1-sol, Engineers p105 and p115. Adapted bodies: none.
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
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// RVA 0x266030, 84 bytes: BGSProjectile::UnClone3D
// RVA 0x266430, 193 bytes: BGSProjectile::GetActivateText
// RVA 0x2656c0, 197 bytes: BGSProjectile::InitializeData
#include "BGSProjectile.h"
inline bool TestBit(std::uint32_t flags,std::uint32_t bit) { return ((flags>>bit)&1)!=0; }
void BGSProjectile::UnClone3D(TESObjectREFR* ref) { UnCloneProjectile(this,ref); if(ref && ((projectileData.flagsAndType&0x7f0000)==0x40000 || !static_cast<Projectile*>(ref)->inventoryEntry || !*static_cast<void**>(static_cast<Projectile*>(ref)->inventoryEntry))) RemoveProjectileClone(this,ref); }
bool BGSProjectile::GetActivateText(TESObjectREFR* ref,BSString& text) { std::int32_t count=ref?ProjectileCount(&ref->extraList):0; if(TestBit(projectileData.flagsAndType,6)) { bool crime=ProjectileCrime(ref); if(count>1) { const char* action=TakeProjectileText; if(crime) action=StealProjectileText; auto* name=ProjectileName(ref); FormatProjectileText(&text,"%s\n%s (%i)",action,name,count); } else { const char* action=TakeProjectileText; if(crime) action=StealProjectileText; auto* name=ProjectileName(ref); FormatProjectileText(&text,"%s\n%s",action,name); } return true; } return false; }

