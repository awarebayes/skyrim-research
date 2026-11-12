// TESNPC member functions, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x3cd8d0, 5 bytes (SetObjectVoiceType); RVA 0x3afeb0, 20 bytes (IsFemale);
// RVA 0x3a4e00, 36 bytes (GetRelationshipRankIndex); RVA 0x3c65c0, 95 bytes (GetScale);
// RVA 0x3c8c00, 238 bytes (HasOverlays).
// Evidence: findings/fourth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) and meh321's Address Library name list; the powerof3
// fork (GPL-3.0) uses the same ones. A byte match shows that this source and recipe produce the
// checked code; it does not verify the community names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions above are compared.
#include "TESNPC.h"

// SetObjectVoiceType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
void TESNPC::SetObjectVoiceType(BGSVoiceType* a_voiceType)
{
	voiceType = a_voiceType;
}

// noinline: GetScale, defined later in this file, calls IsFemale in the image instead of inlining it.
// The two probably come from different original translation units (they lie about 0x16000 bytes
// apart); grouping them in one unit here would let the compiler inline the call, so the attribute
// stands in for that unit boundary.
__declspec(noinline) std::int32_t TESNPC::IsFemale()
{
	// form type 0x2b is the NPC form type; other forms report -1
	if (formType == 0x2B) {
		return static_cast<std::uint8_t>(actorBaseFlags) & 1;
	}
	return -1;
}

// GetRelationshipRankIndex: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
std::int32_t TESNPC::GetRelationshipRankIndex(TESNPC* a_npc1, TESNPC* a_npc2)
{
	BGSRelationship* relationship = BGSRelationship::GetRelationship(a_npc1, a_npc2);
	if (relationship) {
		return relationship->rankBits & 0x7FFFFFFF;
	}
	return 4;
}

float TESNPC::GetScale()
{
	float scale = 1.0f;
	if (race) {
		std::int32_t sex = IsFemale();
		if (static_cast<std::uint32_t>(sex) <= 1) {
			scale = race->height[sex];
		} else {
			scale = 0.0f;
		}
	}
	return scale * height;
}

// FindOverlays: GUESS(low); the table lookup is inlined into each overlay accessor and writes the
// out-parameter only on a hit
// hot path: the engine inlines this table lookup at every overlay accessor
static __forceinline bool FindOverlays(const void* a_key, BSTArray<BGSHeadPart*>*& a_value)
{
	std::uint32_t hash;
	CRC32Calculator::SizeOf64(hash, reinterpret_cast<std::uint64_t>(a_key));
	OverlayEntry* entries = g_overlayEntries;
	if (!entries) {
		return false;
	}
	std::uint32_t index = (g_overlayCapacity - 1) & hash;
	OverlayEntry* entry = &entries[index];
	if (!entry->next) {
		return false;
	}
	do {
		if (entry->key == a_key) {
			a_value = entry->value;
			return true;
		}
		entry = entry->next;
	} while (entry != g_overlaySentinel);
	return false;
}

bool TESNPC::HasOverlays()
{
	if (formID == 7 && PlayerCharacter::singleton) {
		BSTArray<BGSHeadPart*>* overlays = nullptr;
		FindOverlays(GetPlayerBaseNPC(PlayerCharacter::singleton), overlays);
		TESRace* playerRace = PlayerCharacter::singleton->unkB48;
		return playerRace && playerRace != race && overlays;
	}
	return originalRace && originalRace != race;
}
