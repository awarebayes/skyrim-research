// BSTimer::SetGlobalTimeMultiplier, build sse-steam-1-7-104, RVA 0xce3970, 76 bytes.
//
// Evidence: findings/second-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from a local instruction listing and
// decompiler output of the pinned image, with types from the header beside this file.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method name or that the original source looked like this.
// Recipe: reconstruction/recipes/o2-fpfast.json (compile this file alone, /Gy required). /fp:fast
// because the target has no NaN parity branch after its float inequality test; /fp:precise
// emits one.
// Only SetGlobalTimeMultiplier is compared.
#include "BSTimer.h"

void BSTimer::SetGlobalTimeMultiplier(float a_multiplier, bool a_arg2)
{
    // The flag is read before the global store: bool aliases any object, so the store would
    // otherwise force a reload after it.
    const bool useTarget = useGlobalTimeMultiplierTarget;
    QGlobalTimeMultiplierTarget = a_multiplier;
    if (useTarget) {
        if (a_arg2) {
            QGlobalTimeMultiplier = a_multiplier;
        }
    } else if (a_multiplier != QGlobalTimeMultiplier) {
        delta /= QGlobalTimeMultiplier;
        QGlobalTimeMultiplier = a_multiplier;
        delta *= a_multiplier;
    }
}
