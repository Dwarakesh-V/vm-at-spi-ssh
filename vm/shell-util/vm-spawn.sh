# Virtual machine initialization
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

# Load virtual machine from saved state
qemu-system-x86_64 \
  -enable-kvm \
  -cpu host \
  -m 4096 \
  -smp 2 \
  -drive id=drive0,file=vm-at1.qcow2,format=qcow2,if=none \
  -netdev user,id=net0,hostfwd=tcp::2222-:22 \
  -device virtio-net-pci,netdev=net0 \
  -device virtio-blk-pci,drive=drive0 \
  -device virtio-gpu-pci \
  -chardev socket,id=ch0,path=/tmp/vm-channel.sock,server=on,wait=off \
  -device virtio-serial \
  -device virtserialport,chardev=ch0,name=host.guest.0 \
  -monitor stdio \
  -display gtk
