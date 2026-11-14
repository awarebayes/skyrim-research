// Build: sse-steam-1-7-104; RVA 0xce90a0; 52 bytes
// Evidence: findings/ghidra-import.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Source exposure: binary-analysis
// Drafted by tools/deleting_wrapper_template_v1.py (GPT-6.1 Sol).
// Labels: v2
// DeletingWrapperce90a0, object: GUESS(low) STANDIN
// Interface has a virtual destructor and no represented data members.
// Original ownership and additional virtual methods are not recovered here.
// The complete destructor is external and independently bound for this member.
// Only the compiler-emitted scalar deleting destructor is compared.
// Global object requests normal virtual-table and wrapper emission.
// No external implementation is copied; a pass proves no name or original layout.
// Origin: {"family": "scalar-deleting-eight-byte-wrapper", "template_digest": "f96fd9782e169a414a5460b1a9d6e9acb5133f20652acdb23cbf4f7cd78e3e52", "version": "1"}
#include "DeletingWrapperce90a0.h"
static DeletingWrapperce90a0 object;
