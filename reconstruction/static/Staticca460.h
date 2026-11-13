// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticca460, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticca460;
extern void construct(Staticca460*, const Descriptor*);
extern void destroy(Staticca460*);
struct Staticca460 {
    void* value;
    Staticca460() { construct(this, &descriptor); }
    ~Staticca460() { destroy(this); }
};
