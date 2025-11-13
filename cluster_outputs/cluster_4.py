# Cluster 4

def main():
    data_dir = 'autoencoder/dataset/'
    writer = SummaryWriter(f'runs/' + 'auto-encoder')
    train_transforms = transforms.Compose([transforms.RandomRotation(30), transforms.RandomHorizontalFlip(), transforms.ToTensor()])
    test_transforms = transforms.Compose([transforms.ToTensor()])
    train_data = datasets.ImageFolder(data_dir + 'train', transform=train_transforms)
    test_data = datasets.ImageFolder(data_dir + 'test', transform=test_transforms)
    m = len(train_data)
    train_data, val_data = random_split(train_data, [int(m - m * 0.2), int(m * 0.2)])
    trainloader = torch.utils.data.DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)
    validloader = torch.utils.data.DataLoader(val_data, batch_size=BATCH_SIZE, shuffle=True)
    testloader = torch.utils.data.DataLoader(test_data, batch_size=BATCH_SIZE)
    model = VariationalAutoencoder(latent_dims=LATENT_SPACE).to(device)
    optim = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    print(f'Selected device :) :) :) {device}')
    for epoch in range(NUM_EPOCHS):
        train_loss = train(model, trainloader, optim)
        writer.add_scalar('Training Loss/epoch', train_loss, epoch + 1)
        val_loss = test(model, validloader)
        writer.add_scalar('Validation Loss/epoch', val_loss, epoch + 1)
        print('\nEPOCH {}/{} \t train loss {:.3f} \t val loss {:.3f}'.format(epoch + 1, NUM_EPOCHS, train_loss, val_loss))
    model.save()

def main():
    data_dir = 'autoencoder/dataset/'
    test_transforms = transforms.Compose([transforms.ToTensor()])
    test_data = datasets.ImageFolder(data_dir + 'test', transform=test_transforms)
    testloader = torch.utils.data.DataLoader(test_data, batch_size=BATCH_SIZE)
    model = VariationalAutoencoder(latent_dims=LATENT_SPACE).to(device)
    model.load()
    count = 1
    with torch.no_grad():
        for x, _ in testloader:
            x = x.to(device)
            x_hat = model(x)
            x_hat = x_hat.cpu()
            x_hat = x_hat.squeeze(0)
            transform = transforms.ToPILImage()
            img = transform(x_hat)
            image_filename = str(count) + '.png'
            img.save('autoencoder/reconstructed/' + image_filename)
            count += 1

