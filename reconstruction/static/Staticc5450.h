// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Staticc5450, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Staticc5450;
extern void construct(Staticc5450*, const Descriptor*);
extern void destroy(Staticc5450*);
struct Staticc5450 {
    void* value;
    Staticc5450() { construct(this, &descriptor); }
    ~Staticc5450() { destroy(this); }
};
