# Finding: fifth batch of 223 functions in 99 classes, chosen for a low cost per function

Status: OBSERVED properties of the pinned image; selection only. Nothing reconstructed or compared.
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5), task p16-batch5-prep; local only
Date (UTC): 2026-11-12
Target build id / image SHA-256: `sse-steam-1-7-104` / `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`
Function RVA / size (if applicable): private plan `.local/packs/_plan/fifth-batch/` (list, plan, inventory rows)
Source exposure: mixed (binary-analysis of the pinned image: its .pdata, EH, RTTI and code bytes through the private function table; community-headers; community name databases; the FNV sibling index)
Sources and immutable revisions / licenses: CharmedBaryon/CommonLibSSE-NG `b93280e832f263dbef44e44cbe2936622a02f91a` (MIT); powerof3/CommonLibSSE `654e55f7979c1733033d5dbef176e43827bac944` (GPL-3.0; files carrying its declarations state GPL-3.0); Address Library 1.7.104.0; meh321's name list `skyrimae.rename`, used with the author's permission as reported by the maintainer (`docs/authorizations.md`); momusdigital/fnv_decomp `91e1b6e8` (no licence; used by maintainer decision, pointers only)
Name provenance: COMMUNITY (unverified), class names EXE_RTTI
Confidence: high for counts and the filters; medium for class attribution; low to medium for names; the expected pass rate is a guess from the fourth batch

## Question and method

Which functions should the next Drafter wave take so that one Drafter covers many functions at a
low cost each? A Drafter run has a fixed start-up cost and a per-function cost; in the fourth batch
small functions passed in one or two attempts. `export_pack.py plan --order cheap`
(`tools/ghidra/plan_cheap.py`) starts from the whole-image table of `build_function_table.py` and
keeps ordinary, v2-ready, community-named functions of classes that pass the per-class checks
(`findings/fourth-batch-selection.md`), and then also requires:

- at most 500 bytes, no exception-handling data (no language handler at all);
- no thread-local read: the function's bytes are scanned for the `gs:[0x58]` load that starts
  every `__declspec(thread)` access in this image;
- not in the two parked families of the census in `findings/whole-program-optimization.md`
  (callee-saved saves that skip the first home slot; an EH state store without a handler);
- a class whose skeleton is verified (a community header passes C1 to C3 and the size is read from
  the deleting destructor, C4);
- no class that already has a unit in `reconstruction/` or an open task: extending an accepted
  unit re-opens its records, and two tasks on one unit would collide.

Ranking: an FNV counterpart (a same-named method, or an agreeing slot, in the sibling index; one
more point for an optimised `/O2` counterpart), a class with entries in the FNV inline-helper
catalogue, size (at most 64 bytes first, then at most 128), a base class whose header already exists
in `reconstruction/`, then fan-in. One function per L1 cluster: the other members are the stamping
lane's. Then grouping: classes with at least six selected functions, most of them over 64 bytes,
become **normal** tasks (one class, 6 to 10 functions); the small functions of the remaining
classes form **small** tasks of 15 to 25 functions, one unit per class, grouped under the nearest
common RTTI base that gathers at least 15 of them. 60 functions were reserved for normal tasks.

## Observations

- Eligible after all filters: 1,579 functions; 982 after one per L1 cluster. Removed by the new
  filters (after the existing ones): exception data 539, existing unit or open task 706, no verified
  skeleton 213, parked family 34, thread-local read 12 (183 of the 3,083 scanned functions read
  thread-local data; most were already out for other reasons), families too small for a task 91.
- Selected: **223 functions, 11,290 bytes, 99 classes**, in 15 tasks: 8 small (168 functions, 92
  units) and 7 normal (55 functions), plus the ten undrafted fourth-batch tasks (68 functions, 6,543
  bytes) for a wave of 291 functions.
- Size bands: at most 32 bytes 98; 33 to 64 86; 65 to 128 22; 129 to 256 15; 257 to 512 2.
- Areas (prefix rule): forms 136, netimmerse 59, bsengine 28.
- FNV: 49 functions have a counterpart in the sibling index (26 of them `/O2`); 140 sit in a class
  with inline-helper catalogue entries; 152 have one or the other.
- Clusters: 73 of the 223 are members of an L1 cluster with more than one member (each the only one
  of its cluster in the batch).
- Name sources of the first usable name: NG slot 166, po3 slot 35, meh321 16, po3 id 4, NG id 2.
- One normal task (`NiPointLight`) holds two functions that test float equality without a parity
  branch; its other functions are recipe-neutral, so the task uses the `o2-fpfast` recipe.

| task kind | tasks | units | functions | bytes | budget (counted attempts) |
|---|---|---|---|---|---|
| small | 8 | 92 | 168 | 5,087 | 383 |
| normal | 7 | 7 | 55 | 6,203 | 193 |

## Interpretation and alternatives

Most of the batch is accessors, data initialisers and deleting destructors of form components and
scene-graph classes, the shapes that passed fastest before. Classes with an accepted unit were left
out rather than extended, so no record goes stale; their headers are offered to new units instead
(the task brief lists them). An alternative would take more functions from the accepted classes and
re-confirm them with the unit; that costs a Reviewer pass per extended unit while the label-only path
is held to label and comment diffs.

## Units and tasks

Generated from the task directories of this selection: each unit, its task id
and the compared functions whose inventory rows cite this file. Names are the community names the
inventory publishes (unverified).

<!-- unit table: generated by tools/ghidra/export_pack.py evidence-table; do not edit -->

| task id | class | unit | functions (RVA, inventory name) |
|---|---|---|---|
| `batch5-s03-niobject-bsbound` | `BSBound` | `reconstruction/bsengine/BSBound.cpp` | `0xff17c0` `BSBound::LoadBinary` |
| `batch5-s01-niavobject-bscubemapcamera` | `BSCubeMapCamera` | `reconstruction/bsengine/BSCubeMapCamera.cpp` | `0x1559a60` `BSCubeMapCamera::RenderCubemap` |
| `batch5-s01-niavobject-bsfadenode` | `BSFadeNode` | `reconstruction/bsengine/BSFadeNode.cpp` | `0x106b550` `BSFadeNode::UpdateCollisionObject`; `0x14e5a20` `BSFadeNode::ctor`; `0x14e7240` `BSFadeNode::~BSFadeNode` |
| `batch5-s01-niavobject-bsinstancetrishape` | `BSInstanceTriShape` | `reconstruction/bsengine/BSInstanceTriShape.cpp` | `0xfe4240` `BSInstanceTriShape::~BSInstanceTriShape` |
| `batch5-s03-niobject-bsinvmarker` | `BSInvMarker` | `reconstruction/bsengine/BSInvMarker.cpp` | `0xfff1d0` `BSInvMarker::~BSInvMarker` |
| `batch5-s01-niavobject-bsmultiboundnode` | `BSMultiBoundNode` | `reconstruction/bsengine/BSMultiBoundNode.cpp` | `0xff2bc0` `BSMultiBoundNode::IsEqual` |
| `batch5-s03-niobject-bsmultiboundshape` | `BSMultiBoundShape` | `reconstruction/bsengine/BSMultiBoundShape.cpp` | `0xfe4fb0` `BSMultiBoundShape::ctor` |
| `batch5-s01-niavobject-bsninode` | `BSNiNode` | `reconstruction/bsengine/BSNiNode.cpp` | `0x1005450` `BSNiNode::~BSNiNode` |
| `batch5-s03-niobject-bsocclusionplane` | `BSOcclusionPlane` | `reconstruction/bsengine/BSOcclusionPlane.cpp` | `0xfe9bd0` `BSOcclusionPlane::~BSOcclusionPlane` |
| `batch5-s03-niobject-bsocclusionshape` | `BSOcclusionShape` | `reconstruction/bsengine/BSOcclusionShape.cpp` | `0xfdc610` `BSOcclusionShape::~BSOcclusionShape` |
| `batch5-s01-niavobject-bsorderednode` | `BSOrderedNode` | `reconstruction/bsengine/BSOrderedNode.cpp` | `0x1570700` `BSOrderedNode::OnVisible` |
| `batch5-s03-niobject-bsshaderaccumulator` | `BSShaderAccumulator` | `reconstruction/bsengine/BSShaderAccumulator.cpp` | `0x14ecb90` `BSShaderAccumulator::GetCurrentAccumulator`; `0x14ecba0` `BSShaderAccumulator::SetCurrentAccumulator`; `0x151ef00` `BSShaderAccumulator::FinishAccumulatingPostResolveDepth`; `0x1520d50` `BSShaderAccumulator::StartGroupingAlphas` |
| `batch5-s03-niobject-bsshadertextureset` | `BSShaderTextureSet` | `reconstruction/bsengine/BSShaderTextureSet.cpp` | `0x153b3c0` `BSShaderTextureSet::GetTexturePath` |
| `batch5-s01-niavobject-bsstripparticlesystem` | `BSStripParticleSystem` | `reconstruction/bsengine/BSStripParticleSystem.cpp` | `0xf9fd70` `BSStripParticleSystem::~BSStripParticleSystem` |
| `batch5-s03-niobject-bstempeffectdebris` | `BSTempEffectDebris` | `reconstruction/bsengine/BSTempEffectDebris.cpp` | `0x4aa860` `BSTempEffectDebris::Get3D` |
| `batch5-s03-niobject-bstempeffectgeometrydecal` | `BSTempEffectGeometryDecal` | `reconstruction/bsengine/BSTempEffectGeometryDecal.cpp` | `0x4adc40` `BSTempEffectGeometryDecal::~BSTempEffectGeometryDecal` |
| `batch5-s03-niobject-bstempeffectspg` | `BSTempEffectSPG` | `reconstruction/bsengine/BSTempEffectSPG.cpp` | `0x4b5250` `BSTempEffectSPG::FinishLoadGame`; `0x4b5800` `BSTempEffectSPG::GetType` |
| `batch5-s03-niobject-bstempeffectsimpledecal` | `BSTempEffectSimpleDecal` | `reconstruction/bsengine/BSTempEffectSimpleDecal.cpp` | `0x4b1090` `BSTempEffectSimpleDecal::Initialize`; `0x4b2950` `BSTempEffectSimpleDecal::Get3D`; `0x4b4a40` `BSTempEffectSimpleDecal::~BSTempEffectSimpleDecal` |
| `batch5-s03-niobject-bsterraineffect` | `BSTerrainEffect` | `reconstruction/bsengine/BSTerrainEffect.cpp` | `0x4b7c40` `BSTerrainEffect::GetManagerHandlesSaveLoad` |
| `batch5-s01-niavobject-bstrishape` | `BSTriShape` | `reconstruction/bsengine/BSTriShape.cpp` | `0xef2120` `BSTriShape::IsEqual` |
| `batch5-s04-baseformcomponent-bgsblockbashdata` | `BGSBlockBashData` | `reconstruction/forms/BGSBlockBashData.cpp` | `0x1d2240` `BGSBlockBashData::InitializeDataComponent` |
| `batch5-s08-tesform-bgscamerapath` | `BGSCameraPath` | `reconstruction/forms/BGSCameraPath.cpp` | `0x316110` `BGSCameraPath::InitializeData`; `0x317ce0` `BGSCameraPath::~BGSCameraPath` |
| `batch5-s08-tesform-bgscamerashot` | `BGSCameraShot` | `reconstruction/forms/BGSCameraShot.cpp` | `0x318c10` `BGSCameraShot::InitializeData`; `0x31a0c0` `BGSCameraShot::~BGSCameraShot` |
| `batch5-s08-tesform-bgscollisionlayer` | `BGSCollisionLayer` | `reconstruction/forms/BGSCollisionLayer.cpp` | `0x31aa10` `BGSCollisionLayer::ClearData`; `0x31aa50` `BGSCollisionLayer::GetCollidesWithMask` |
| `batch5-s08-tesform-bgscolorform` | `BGSColorForm` | `reconstruction/forms/BGSColorForm.cpp` | `0x31b530` `BGSColorForm::InitializeData` |
| `batch5-s08-tesform-bgsconstructibleobject` | `BGSConstructibleObject` | `reconstruction/forms/BGSConstructibleObject.cpp` | `0x25de90` `BGSConstructibleObject::ClearData` |
| `batch5-s01-niavobject-bgsdecalnode` | `BGSDecalNode` | `reconstruction/forms/BGSDecalNode.cpp` | `0x2030b0` `BGSDecalNode::CreateClone`; `0x203360` `BGSDecalNode::AttachDecal` |
| `batch5-s04-baseformcomponent-bgsdestructibleobjectform` | `BGSDestructibleObjectForm` | `reconstruction/forms/BGSDestructibleObjectForm.cpp` | `0x1d2750` `BGSDestructibleObjectForm::InitializeDataComponent`; `0x1d2760` `BGSDestructibleObjectForm::ClearDataComponent` |
| `batch5-s08-tesform-bgsdialoguebranch` | `BGSDialogueBranch` | `reconstruction/forms/BGSDialogueBranch.cpp` | `0x38cac0` `BGSDialogueBranch::InitializeData` |
| `batch5-bgsencounterzone` | `BGSEncounterZone` | `reconstruction/forms/BGSEncounterZone.cpp` | `0x28f5e0` `BGSEncounterZone::InitializeData`; `0x28f850` `BGSEncounterZone::InitItemImpl`; `0x28f9e0` `BGSEncounterZone::GetLevel`; `0x28fbc0` `BGSEncounterZone::SaveGame`; `0x28fc40` `BGSEncounterZone::LoadGame`; `0x28fcb0` `BGSEncounterZone::Revert`; `0x28fe70` `BGSEncounterZone::~BGSEncounterZone` |
| `batch5-s08-tesform-bgsequipslot` | `BGSEquipSlot` | `reconstruction/forms/BGSEquipSlot.cpp` | `0x38f480` `BGSEquipSlot::InitializeData` |
| `batch5-s04-baseformcomponent-bgsequiptype` | `BGSEquipType` | `reconstruction/forms/BGSEquipType.cpp` | `0x146700` `BGSEquipType::GetEquipSlot`; `0x146a50` `BGSEquipType::SetEquipSlot` |
| `batch5-s08-tesform-bgsfootstep` | `BGSFootstep` | `reconstruction/forms/BGSFootstep.cpp` | `0x31cac0` `BGSFootstep::~BGSFootstep` |
| `batch5-s08-tesform-bgsheadpart` | `BGSHeadPart` | `reconstruction/forms/BGSHeadPart.cpp` | `0x391020` `BGSHeadPart::GetFormEditorID`; `0x391210` `BGSHeadPart::SetFormEditorID` |
| `batch5-s04-baseformcomponent-bgsidlecollection` | `BGSIdleCollection` | `reconstruction/forms/BGSIdleCollection.cpp` | `0x1d75f0` `BGSIdleCollection::Ctor`; `0x1d76e0` `BGSIdleCollection::InitializeDataComponent` |
| `batch5-s08-tesform-bgsimpactdata` | `BGSImpactData` | `reconstruction/forms/BGSImpactData.cpp` | `0x31d7b0` `BGSImpactData::InitializeData` |
| `batch5-s08-tesform-bgskeyword` | `BGSKeyword` | `reconstruction/forms/BGSKeyword.cpp` | `0x29e710` `BGSKeyword::GetFormEditorID` |
| `batch5-s08-tesform-bgslightingtemplate` | `BGSLightingTemplate` | `reconstruction/forms/BGSLightingTemplate.cpp` | `0x2955d0` `BGSLightingTemplate::InitializeData` |
| `batch5-s08-tesform-bgslocation` | `BGSLocation` | `reconstruction/forms/BGSLocation.cpp` | `0x2984a0` `BGSLocation::InitializeData`; `0x29cd00` `BGSLocation::~BGSLocation` |
| `batch5-s08-tesform-bgsmaterialobject` | `BGSMaterialObject` | `reconstruction/forms/BGSMaterialObject.cpp` | `0x321740` `BGSMaterialObject::EnsureLoaded`; `0x321c34` `BGSMaterialObject::dtor` |
| `batch5-s06-baseformcomponent-bgsmovablestatic` | `BGSMovableStatic` | `reconstruction/forms/BGSMovableStatic.cpp` | `0x2640a0` `BGSMovableStatic::InitializeData`; `0x264444` `BGSMovableStatic::dtor` |
| `batch5-s08-tesform-bgsmusictrackformwrapper` | `BGSMusicTrackFormWrapper` | `reconstruction/forms/BGSMusicTrackFormWrapper.cpp` | `0x327430` `BGSMusicTrackFormWrapper::InitItemImpl` |
| `batch5-s08-tesform-bgsmusictype` | `BGSMusicType` | `reconstruction/forms/BGSMusicType.cpp` | `0x327e40` `BGSMusicType::DoPause`; `0x328550` `BGSMusicType::GetFormEditorID`; `0x328570` `BGSMusicType::SetFormEditorID`; `0x328688` `BGSMusicType::dtor` |
| `batch5-s04-baseformcomponent-bgsoverridepackcollection` | `BGSOverridePackCollection` | `reconstruction/forms/BGSOverridePackCollection.cpp` | `0x1daad0` `BGSOverridePackCollection::InitializeDataComponent`; `0x1db070` `BGSOverridePackCollection::~BGSOverridePackCollection` |
| `batch5-s04-baseformcomponent-bgsperkrankarray` | `BGSPerkRankArray` | `reconstruction/forms/BGSPerkRankArray.cpp` | `0x1db110` `BGSPerkRankArray::ClearDataComponent` |
| `batch5-s05-tesform-bgsstorymanagerbranchnode` | `BGSStoryManagerBranchNode` | `reconstruction/forms/BGSStoryManagerBranchNode.cpp` | `0x1c7cd0` `BGSStoryManagerBranchNode::GetChild`; `0x1c8500` `BGSStoryManagerBranchNode::QChildCount`; `0x5358d0` `BGSStoryManagerBranchNode::InitItemImpl` |
| `batch5-s05-tesform-bgsstorymanagereventnode` | `BGSStoryManagerEventNode` | `reconstruction/forms/BGSStoryManagerEventNode.cpp` | `0x535c10` `BGSStoryManagerEventNode::InitializeData`; `0x535d60` `BGSStoryManagerEventNode::GetFormEditorID` |
| `batch5-s05-tesform-bgsstorymanagernodebase` | `BGSStoryManagerNodeBase` | `reconstruction/forms/BGSStoryManagerNodeBase.cpp` | `0x1c8520` `BGSStoryManagerNodeBase::QConditions`; `0x5360f0` `BGSStoryManagerNodeBase::InitializeData` |
| `batch5-s05-tesform-bgsstorymanagerquestnode` | `BGSStoryManagerQuestNode` | `reconstruction/forms/BGSStoryManagerQuestNode.cpp` | `0x539020` `BGSStoryManagerQuestNode::Revert` |
| `batch5-s07-tesobjectacti-bgstalkingactivator` | `BGSTalkingActivator` | `reconstruction/forms/BGSTalkingActivator.cpp` | `0x2671e0` `BGSTalkingActivator::InitializeData`; `0x267460` `BGSTalkingActivator::SaveGame`; `0x267530` `BGSTalkingActivator::Revert`; `0x2676a0` `BGSTalkingActivator::GetObjectVoiceType`; `0x267810` `BGSTalkingActivator::SetObjectVoiceType` |
| `batch5-s06-baseformcomponent-bgstexturemodel` | `BGSTextureModel` | `reconstruction/forms/BGSTextureModel.cpp` | `0x3eb800` `BGSTextureModel::~BGSTextureModel` |
| `batch5-s04-baseformcomponent-tesaiform` | `TESAIForm` | `reconstruction/forms/TESAIForm.cpp` | `0x1de800` `TESAIForm::InitializeDataComponent`; `0x1de820` `TESAIForm::ClearDataComponent` |
| `batch5-s04-baseformcomponent-tesactorbasedata` | `TESActorBaseData` | `reconstruction/forms/TESActorBaseData.cpp` | `0x1dc5e0` `TESActorBaseData::InitializeDataComponent`; `0x1dc630` `TESActorBaseData::ClearDataComponent`; `0x1de5c0` `TESActorBaseData::GetInvulnerable`; `0x1de5d0` `TESActorBaseData::GetIsGhost`; `0x1de5e0` `TESActorBaseData::Unk_07`; `0x1de5f0` `TESActorBaseData::GetVoiceType` |
| `batch5-s04-baseformcomponent-tesattackdamageform` | `TESAttackDamageForm` | `reconstruction/forms/TESAttackDamageForm.cpp` | `0x1df0c0` `TESAttackDamageForm::InitializeDataComponent`; `0x1df130` `TESAttackDamageForm::GetAttackDamage`; `0x1df1a0` `TESAttackDamageForm::~TESAttackDamageForm` |
| `batch5-s02-tesform-tescombatstyle` | `TESCombatStyle` | `reconstruction/forms/TESCombatStyle.cpp` | `0x26a160` `TESCombatStyle::InitItemImpl`; `0x26a890` `TESCombatStyle::~TESCombatStyle` |
| `batch5-s04-baseformcomponent-tescontainer` | `TESContainer` | `reconstruction/forms/TESContainer.cpp` | `0x1e0b10` `TESContainer::GetItemCount` |
| `batch5-s04-baseformcomponent-tesdescription` | `TESDescription` | `reconstruction/forms/TESDescription.cpp` | `0x1e1240` `TESDescription::InitializeDataComponent` |
| `batch5-s02-tesform-teseffectshader` | `TESEffectShader` | `reconstruction/forms/TESEffectShader.cpp` | `0x26b3e0` `TESEffectShader::InitializeData` |
| `batch5-s06-baseformcomponent-tesenchantableform` | `TESEnchantableForm` | `reconstruction/forms/TESEnchantableForm.cpp` | `0x1e1e60` `TESEnchantableForm::InitializeDataComponent`; `0x1e20a0` `TESEnchantableForm::~TESEnchantableForm`; `0x1e20d0` `TESEnchantableForm::GetCastingType` |
| `batch5-s02-tesform-teseyes` | `TESEyes` | `reconstruction/forms/TESEyes.cpp` | `0x3b2fb0` `TESEyes::InitializeData` |
| `batch5-s07-tesobjectacti-tesflora` | `TESFlora` | `reconstruction/forms/TESFlora.cpp` | `0x26da40` `TESFlora::InitItemImpl`; `0x26da90` `TESFlora::Activate` |
| `batch5-s06-baseformcomponent-tesfullname` | `TESFullName` | `reconstruction/forms/TESFullName.cpp` | `0x146720` `TESFullName::GetFullName` |
| `batch5-s07-tesobjectacti-tesfurniture` | `TESFurniture` | `reconstruction/forms/TESFurniture.cpp` | `0x26e110` `TESFurniture::InitializeData`; `0x26e130` `TESFurniture::ClearData`; `0x26ed80` `TESFurniture::Clone3D` |
| `batch5-s02-tesform-tesglobal` | `TESGlobal` | `reconstruction/forms/TESGlobal.cpp` | `0x340be0` `TESGlobal::GetFormEditorID`; `0x340c00` `TESGlobal::SetFormEditorID` |
| `batch5-s02-tesform-tesidleform` | `TESIdleForm` | `reconstruction/forms/TESIdleForm.cpp` | `0x3b8200` `TESIdleForm::~TESIdleForm` |
| `batch5-s02-tesform-tesimagespacemodifier` | `TESImageSpaceModifier` | `reconstruction/forms/TESImageSpaceModifier.cpp` | `0x2a8df0` `TESImageSpaceModifier::~TESImageSpaceModifier`; `0x2a8e30` `TESImageSpaceModifier::GetFormEditorID`; `0x2a8e70` `TESImageSpaceModifier::SetFormEditorID` |
| `batch5-s06-baseformcomponent-tesleveledlist` | `TESLeveledList` | `reconstruction/forms/TESLeveledList.cpp` | `0x1e8850` `TESLeveledList::InitializeDataComponent`; `0x1e8880` `TESLeveledList::GetChanceNone`; `0x1e88f0` `TESLeveledList::GetMultCalc`; `0x1e8930` `TESLeveledList::GetUseAll` |
| `batch5-s02-tesform-tesloadscreen` | `TESLoadScreen` | `reconstruction/forms/TESLoadScreen.cpp` | `0x340ec0` `TESLoadScreen::ClearData` |
| `batch5-s06-baseformcomponent-tesmodeltextureswap` | `TESModelTextureSwap` | `reconstruction/forms/TESModelTextureSwap.cpp` | `0x1ecd70` `TESModelTextureSwap::InitializeDataComponent` |
| `batch5-s07-tesobjectacti-tesobjectacti` | `TESObjectACTI` | `reconstruction/forms/TESObjectACTI.cpp` | `0x267690` `TESObjectACTI::GetIgnoredBySandbox`; `0x2677d0` `TESObjectACTI::GetWaterType`; `0x279750` `TESObjectACTI::InitializeData`; `0x279ce0` `TESObjectACTI::InitItemImpl`; `0x27a690` `TESObjectACTI::IsWater` |
| `batch5-s02-tesform-tesobjectanio` | `TESObjectANIO` | `reconstruction/forms/TESObjectANIO.cpp` | `0x27b9b0` `TESObjectANIO::InitItemImpl`; `0x27bb70` `TESObjectANIO::GetFormEditorID` |
| `batch5-s02-tesform-tesobjectland` | `TESObjectLAND` | `reconstruction/forms/TESObjectLAND.cpp` | `0x2a9130` `TESObjectLAND::CreateDuplicateForm`; `0x2aa2e0` `TESObjectLAND::SetAltered` |
| `batch5-tespackage` | `TESPackage` | `reconstruction/forms/TESPackage.cpp` | `0x498940` `TESPackage::ClearData`; `0x49d500` `TESPackage::SaveGame`; `0x49d7a0` `TESPackage::Revert`; `0x49e270` `TESPackage::GetObjectTypeName`; `0x49e890` `TESPackage::~TESPackage`; `0x49e8d0` `TESPackage::GetRefCount` |
| `batch5-s06-baseformcomponent-tesproduceform` | `TESProduceForm` | `reconstruction/forms/TESProduceForm.cpp` | `0x1ee470` `TESProduceForm::InitializeDataComponent`; `0x1eee40` `TESProduceForm::~TESProduceForm` |
| `batch5-s05-tesform-tesquest` | `TESQuest` | `reconstruction/forms/TESQuest.cpp` | `0x3ce410` `TESQuest::InitializeData`; `0x3d2870` `TESQuest::FinishLoadGame`; `0x3d31f0` `TESQuest::GetAlias`; `0x3dedb0` `TESQuest::~TESQuest`; `0x3df9b0` `TESQuest::GetFormEditorID`; `0x3dfeb0` `TESQuest::QConditions` |
| `batch5-s02-tesform-tesrace` | `TESRace` | `reconstruction/forms/TESRace.cpp` | `0x3e6250` `TESRace::GetBodyPartData`; `0x3e64a0` `TESRace::GetMovementType`; `0x3eb840` `TESRace::~TESRace`; `0x3ebd80` `TESRace::GetFormEditorID`; `0x3ebda0` `TESRace::GetPlayable` |
| `batch5-s06-baseformcomponent-tesraceform` | `TESRaceForm` | `reconstruction/forms/TESRaceForm.cpp` | `0x1ef750` `TESRaceForm::CopyComponent` |
| `batch5-s06-baseformcomponent-tesreactionform` | `TESReactionForm` | `reconstruction/forms/TESReactionForm.cpp` | `0x1ef9c0` `TESReactionForm::InitializeDataComponent` |
| `batch5-s02-tesform-tesshout` | `TESShout` | `reconstruction/forms/TESShout.cpp` | `0x387ea0` `TESShout::GetKnown` |
| `batch5-s06-baseformcomponent-testexture1024` | `TESTexture1024` | `reconstruction/forms/TESTexture1024.cpp` | `0x309f20` `TESTexture1024::GetMaxAllowedSize` |
| `batch5-s02-tesform-testopic` | `TESTopic` | `reconstruction/forms/TESTopic.cpp` | `0x3eee90` `TESTopic::IsFormTypeChild` |
| `batch5-s02-tesform-testopicinfo` | `TESTopicInfo` | `reconstruction/forms/TESTopicInfo.cpp` | `0x3f3150` `TESTopicInfo::LoadGame`; `0x3f3180` `TESTopicInfo::Revert` |
| `batch5-s05-tesform-teswaterform` | `TESWaterForm` | `reconstruction/forms/TESWaterForm.cpp` | `0x306f80` `TESWaterForm::GetDangerous`; `0x3078e0` `TESWaterForm::~TESWaterForm` |
| `batch5-s06-baseformcomponent-tesweightform` | `TESWeightForm` | `reconstruction/forms/TESWeightForm.cpp` | `0x1f3760` `TESWeightForm::CopyComponent` |
| `batch5-s03-niobject-niaccumulator` | `NiAccumulator` | `reconstruction/netimmerse/NiAccumulator.cpp` | `0xf1ede0` `NiAccumulator::FinishAccumulating`; `0xf1ee00` `NiAccumulator::~NiAccumulator` |
| `batch5-s03-niobject-nialphaaccumulator` | `NiAlphaAccumulator` | `reconstruction/netimmerse/NiAlphaAccumulator.cpp` | `0xf0f290` `NiAlphaAccumulator::IsEqual`; `0xf0f4a0` `NiAlphaAccumulator::~NiAlphaAccumulator` |
| `batch5-s03-niobject-nibooleanextradata` | `NiBooleanExtraData` | `reconstruction/netimmerse/NiBooleanExtraData.cpp` | `0xf0ff60` `NiBooleanExtraData::IsEqual` |
| `batch5-s01-niavobject-nicamera` | `NiCamera` | `reconstruction/netimmerse/NiCamera.cpp` | `0xef1770` `NiCamera::UpdateWorldData`; `0xef1950` `NiCamera::UpdateWorldBound`; `0xef1a10` `NiCamera::~NiCamera` |
| `batch5-s01-niavobject-nidirectionallight` | `NiDirectionalLight` | `reconstruction/netimmerse/NiDirectionalLight.cpp` | `0xf045c0` `NiDirectionalLight::UpdateWorldData`; `0xf046d0` `NiDirectionalLight::~NiDirectionalLight` |
| `batch5-nigeometry` | `NiGeometry` | `reconstruction/netimmerse/NiGeometry.cpp` | `0xf0ad10` `NiGeometry::RegisterStreamables`; `0xf0adb0` `NiGeometry::SaveBinary`; `0xf0b010` `NiGeometry::UpdateDownwardPass`; `0xf0b050` `NiGeometry::UpdateSelectedDownwardPass`; `0xf0b140` `NiGeometry::Unk_36`; `0xf0b150` `NiGeometry::Unk_37`; `0xf0b7f0` `NiGeometry::Unk_3A`; `0xf0b9c0` `NiGeometry::PostLinkObject`; `0xf0ba20` `NiGeometry::SetSelectiveUpdateFlags`; `0xf0cbd0` `NiGeometry::GetRTTI` |
| `batch5-s01-niavobject-nilight` | `NiLight` | `reconstruction/netimmerse/NiLight.cpp` | `0xeed200` `NiLight::~NiLight` |
| `batch5-s01-niavobject-nimeshparticlesystem` | `NiMeshParticleSystem` | `reconstruction/netimmerse/NiMeshParticleSystem.cpp` | `0xf9eb30` `NiMeshParticleSystem::~NiMeshParticleSystem` |
| `batch5-niparticlesystem` | `NiParticleSystem` | `reconstruction/netimmerse/NiParticleSystem.cpp` | `0xf98f50` `NiParticleSystem::LoadBinary`; `0xf99260` `NiParticleSystem::RegisterStreamables`; `0xf992c0` `NiParticleSystem::SaveBinary`; `0xf99390` `NiParticleSystem::IsEqual`; `0xf99a30` `NiParticleSystem::UpdateDownwardPass`; `0xf99aa0` `NiParticleSystem::UpdateSelectedDownwardPass`; `0xf99ba0` `NiParticleSystem::SetSelectiveUpdateFlags`; `0xf99e20` `NiParticleSystem::UpdateWorldData`; `0xf9a140` `NiParticleSystem::~NiParticleSystem` |
| `batch5-s01-niavobject-niparticles` | `NiParticles` | `reconstruction/netimmerse/NiParticles.cpp` | `0xf05220` `NiParticles::RegisterStreamables` |
| `batch5-nipointlight` | `NiPointLight` | `reconstruction/netimmerse/NiPointLight.cpp` | `0x275600` `NiPointLight::SetLightAttenuation`; `0xefe1f0` `NiPointLight::LoadBinary`; `0xefe2e0` `NiPointLight::SaveBinary`; `0xefe3b0` `NiPointLight::IsEqual`; `0xefe4e0` `NiPointLight::Ctor`; `0xefe5f0` `NiPointLight::~NiPointLight` |
| `batch5-niskininstance` | `NiSkinInstance` | `reconstruction/netimmerse/NiSkinInstance.cpp` | `0xef6f50` `NiSkinInstance::~NiSkinInstance`; `0xf096a0` `NiSkinInstance::LoadBinary`; `0xf09820` `NiSkinInstance::RegisterStreamables`; `0xf098d0` `NiSkinInstance::SaveBinary`; `0xf09990` `NiSkinInstance::IsEqual`; `0xf09ca0` `NiSkinInstance::Unk_25`; `0xf0a690` `NiSkinInstance::Ctor` |
| `batch5-nistream` | `NiStream` | `reconstruction/netimmerse/NiStream.cpp` | `0x19e930` `NiStream::SaveLinkID`; `0xee4140` `NiStream::Save3`; `0xee4300` `NiStream::Load1`; `0xee4c80` `NiStream::RegisterFixedString`; `0xee5060` `NiStream::GetLinkIDFromObject`; `0xee69c0` `NiStream::RegisterObjects`; `0xee6bc0` `NiStream::SaveTopLevelObjects`; `0xee6e40` `NiStream::PreSaveObjectSizeTable`; `0xee6ec0` `NiStream::SaveObjectSizeTable`; `0xee6f60` `NiStream::LoadObjectSizeTable` |
| `batch5-s03-niobject-nitexture` | `NiTexture` | `reconstruction/netimmerse/NiTexture.cpp` | `0xef3ea0` `NiTexture::~NiTexture`; `0xf05970` `NiTexture::Unk_28` |
| `batch5-s01-niavobject-nitribasedgeom` | `NiTriBasedGeom` | `reconstruction/netimmerse/NiTriBasedGeom.cpp` | `0xf1f3f0` `NiTriBasedGeom::Unk_36`; `0xf1f480` `NiTriBasedGeom::~NiTriBasedGeom` |

<!-- end of generated unit table -->

## Reproduction and sanitized evidence

`python3 tools/ghidra/export_pack.py plan --order cheap --label fifth-batch --total 232 --task-prefix
batch5- --parked <census.json> --catalogue <inline-candidates.json> --evidence
findings/fifth-batch-selection.md`, then `export_pack.py packs <list> --class-material
--shared-classes-name _shared-classes.batch5.json --fpfast unit`. Inputs and outputs are private.

## Negative results and limitations

The pass-rate expectation is extrapolated from the fourth batch, not measured. The thread-local scan
sees only the `gs:[0x58]` load in the function's own bytes, not a thread-local access in an inlined
callee's out-of-line part. The parked-family census is per function and dated to the comparator of
that census. Shared-header suggestions are by name; most accepted headers are minimal and may lack
the virtual slots a derived class needs. Rows are added to `data/progress.json` as `mapped`.

## Reviewer and outcome

Not reviewed.
