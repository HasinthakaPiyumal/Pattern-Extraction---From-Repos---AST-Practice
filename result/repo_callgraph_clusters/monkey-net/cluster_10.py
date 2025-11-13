# Cluster 10

def discriminator_loss(discriminator_maps_generated, discriminator_maps_real, loss_weights):
    loss_values = [discriminator_gan_loss(discriminator_maps_generated, discriminator_maps_real, loss_weights['discriminator_gan'])]
    return loss_values

