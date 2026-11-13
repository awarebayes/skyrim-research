"""Family metadata specialization for the internal empty-teardown comparison form.

The shared primitive template's source comment records its emitter origin. This
adapter gives the internal comparison form a distinct family origin so a row
audit cannot combine it with externally defined ordinary leaves. It changes no
generated C++ or extraction rule.
"""
from primitive_leaf_template_v1 import emit as shared_emit


def emit(rva, size):
    emitted = shared_emit(rva, size, 'empty', 'teardown')
    emitted['origin'] = dict(emitted['origin'], family='primitive-empty-teardown-entry')
    return emitted


def extract_parameters(rva, code):
    if code != bytes((194, 0, 0)):
        raise ValueError('unsupported-complete-empty-teardown-shape')
    emit(rva, len(code))
    return {'entry-rva': rva, 'size': len(code), 'kind': 'teardown'}
