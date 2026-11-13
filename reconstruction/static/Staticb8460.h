// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb8460, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb8460;
extern void construct(Staticb8460*, const Descriptor*);
extern void destroy(Staticb8460*);
struct Staticb8460 {
    void* value;
    Staticb8460() { construct(this, &descriptor); }
    ~Staticb8460() { destroy(this); }
};
