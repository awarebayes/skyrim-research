// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static1d710, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static1d710;
extern void construct(Static1d710*, const Descriptor*);
extern void destroy(Static1d710*);
struct Static1d710 {
    void* value;
    Static1d710() { construct(this, &descriptor); }
    ~Static1d710() { destroy(this); }
};
