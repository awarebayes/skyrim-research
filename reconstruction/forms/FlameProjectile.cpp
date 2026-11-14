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
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// RVA 0x7ea200, 79 bytes: FlameProjectile::Constructor
// RVA 0x7eb1c0, 79 bytes: FlameProjectile::LoadGame
// RVA 0x7eb150, 96 bytes: FlameProjectile::SaveGame
// RVA 0x7ea260, 3 bytes: FlameProjectile::Slot164
// RVA 0x7eb510, 52 bytes: FlameProjectile::~FlameProjectile
#include "FlameProjectile.h"
FlameProjectile::FlameProjectile() { formType=static_cast<FormType>(0x43); timers.expirationTimer=0; timers.coneAngle=0; }
void FlameProjectile::LoadGame(BGSLoadFormBuffer* a_buf) { Projectile::LoadGame(a_buf); BGSLoadGameBuffer_LoadDataEndian(a_buf,&timers.expirationTimer,4,4); return BGSLoadGameBuffer_LoadDataEndian(a_buf,&timers.coneAngle,4,4); }
void FlameProjectile::SaveGame(BGSSaveFormBuffer* a_buf) { Projectile::SaveGame(a_buf); BGSSaveGameBuffer_SaveDataEndian(a_buf,&timers.expirationTimer,4,4,0); BGSSaveGameBuffer_SaveDataEndian(a_buf,&timers.coneAngle,4,4,0); }
std::uint8_t FlameProjectile::Slot164() const { return 1; }

