# Cluster 41

class ContactFilter(box_2d.b2ContactFilter):

    def ShouldCollide(self, fixture_a, fixture_b):
        object_a = fixture_a.body.userData
        object_b = fixture_b.body.userData
        if not object_a or not object_b:
            return True
        return object_a.should_collide(object_b) and object_b.should_collide(object_a)

def ShouldCollide(self, fixture_a, fixture_b):
    object_a = fixture_a.body.userData
    object_b = fixture_b.body.userData
    if not object_a or not object_b:
        return True
    return object_a.should_collide(object_b) and object_b.should_collide(object_a)

