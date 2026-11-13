// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static20b00, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static20b00;
extern void construct(Static20b00*, const Descriptor*);
extern void destroy(Static20b00*);
struct Static20b00 {
    void* value;
    Static20b00() { construct(this, &descriptor); }
    ~Static20b00() { destroy(this); }
};
