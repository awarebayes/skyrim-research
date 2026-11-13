// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static10a370, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static10a370;
extern void construct(Static10a370*, const Descriptor*);
extern void destroy(Static10a370*);
struct Static10a370 {
    void* value;
    Static10a370() { construct(this, &descriptor); }
    ~Static10a370() { destroy(this); }
};
