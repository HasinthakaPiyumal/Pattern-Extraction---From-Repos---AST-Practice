# Cluster 2

def inceptionresnetv2(num_classes, loss='softmax', pretrained=True, **kwargs):
    model = InceptionResNetV2(num_classes=num_classes, loss=loss, **kwargs)
    if pretrained:
        model.load_imagenet_weights()
    return model

