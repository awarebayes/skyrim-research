// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static10a450, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static10a450;
extern void construct(Static10a450*, const Descriptor*);
extern void destroy(Static10a450*);
struct Static10a450 {
    void* value;
    Static10a450() { construct(this, &descriptor); }
    ~Static10a450() { destroy(this); }
};
