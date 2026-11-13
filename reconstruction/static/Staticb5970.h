// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb5970, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb5970;
extern void construct(Staticb5970*, const Descriptor*);
extern void destroy(Staticb5970*);
struct Staticb5970 {
    void* value;
    Staticb5970() { construct(this, &descriptor); }
    ~Staticb5970() { destroy(this); }
};
