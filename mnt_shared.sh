# This command must be run from guest to mount shared filesystem
sudo mount -t 9p -o trans=virtio shared /mnt/shared