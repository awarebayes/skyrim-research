// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticd210, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticd210;
extern void construct(Staticd210*, const Descriptor*);
extern void destroy(Staticd210*);
struct Staticd210 {
    void* value;
    Staticd210() { construct(this, &descriptor); }
    ~Staticd210() { destroy(this); }
};
