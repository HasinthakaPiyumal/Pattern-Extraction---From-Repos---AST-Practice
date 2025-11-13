# Cluster 40

class ContactListener(box_2d.b2ContactListener):

    def BeginContact(self, contact):
        object_a = contact.fixtureA.body.userData
        object_b = contact.fixtureB.body.userData
        if object_a:
            object_a.on_contact(object_b)
        if object_b:
            object_b.on_contact(object_a)

def BeginContact(self, contact):
    object_a = contact.fixtureA.body.userData
    object_b = contact.fixtureB.body.userData
    if object_a:
        object_a.on_contact(object_b)
    if object_b:
        object_b.on_contact(object_a)

