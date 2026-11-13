// Build: sse-steam-1-7-104
// Source exposure: binary-analysis
// Owning system unknown. Referenced object names are stand-ins unless labelled otherwise.
// Labels: v2
// Statice5440, Descriptor, descriptor, construct, destroy, object: GUESS(low) STANDIN
#pragma once
struct Descriptor;
extern Descriptor descriptor;
struct Statice5440;
extern void construct(Statice5440*, const Descriptor*);
extern void destroy(Statice5440*);
struct Statice5440 {
    void* value;
    Statice5440() { construct(this, &descriptor); }
    ~Statice5440() { destroy(this); }
};
