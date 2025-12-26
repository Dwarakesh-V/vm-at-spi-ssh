# qemu-system-x86_64 \
#   -enable-kvm \
#   -cpu host \
#   -m 4096 \
#   -smp 2 \
#   -drive id=drive0,file=vm-at1.qcow2,format=qcow2,if=none \
#   -cdrom "./vm-dist/debian-12.iso" \
#   -boot d \
#   -netdev user,id=net0 \
#   -device virtio-net-pci,netdev=net0 \
#   -device virtio-blk-pci,drive=drive0 \
#   -display gtk

qemu-system-x86_64 \
  -enable-kvm \
  -cpu host \
  -m 4096 \
  -smp 2 \
  -drive id=drive0,file=vm-at1.qcow2,format=qcow2,if=none \
  -netdev user,id=net0 \
  -device virtio-net-pci,netdev=net0 \
  -device virtio-blk-pci,drive=drive0 \
  -device virtio-gpu-pci \
  -display gtk
