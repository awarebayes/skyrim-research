// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Static108390, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Static108390;
extern void construct(Static108390*, const Descriptor*);
extern void destroy(Static108390*);
struct Static108390 {
    void* value;
    Static108390() { construct(this, &descriptor); }
    ~Static108390() { destroy(this); }
};
