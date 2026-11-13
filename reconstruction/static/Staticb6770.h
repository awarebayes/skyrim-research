// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticb6770, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticb6770;
extern void construct(Staticb6770*, const Descriptor*);
extern void destroy(Staticb6770*);
struct Staticb6770 {
    void* value;
    Staticb6770() { construct(this, &descriptor); }
    ~Staticb6770() { destroy(this); }
};
