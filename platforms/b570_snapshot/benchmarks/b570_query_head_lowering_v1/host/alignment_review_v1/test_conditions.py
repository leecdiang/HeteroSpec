import struct
import unittest
from conditions import aligned_mask_slab, descriptor, logical_q_addresses, span


class AddressRegression(unittest.TestCase):
    def test_element_alignment_does_not_imply_descriptor_alignment(self):
        self.assertEqual(descriptor(32,64,4),(0,32))
        self.assertEqual(descriptor(252,64,4),(192,60))
        self.assertEqual(descriptor(1028,64,4),(1024,4))

    def test_aligned_root_plus_32_is_conditional(self):
        for a in (4,8,16,32,64,128,256,512,1024,4096):
            for root in (0,2*a,31*a):
                self.assertEqual(descriptor(root+32,a,4)[1],32%a)

    def test_pq_mask_rows_all_offsets(self):
        for n in (63,257):
            for j in range(4):
                offset=4*n*j
                self.assertEqual(offset%4,0)
                self.assertEqual(descriptor(256+offset,64,4)[1],offset%64)

    def test_descriptor_backtracking(self):
        self.assertEqual(descriptor(20,8,12),(8,12))
        with self.assertRaises(ValueError):descriptor(2,4,4)

    def test_q_rebase_preserves_all_logical_bytes(self):
        for q in (1,2,3,4):
            data=b''.join(struct.pack('<I',i) for i in range(128*8*q))
            old=bytes(32)+data;new=data
            for x,y in zip(logical_q_addresses(q,8,32),logical_q_addresses(q,8,0)):
                self.assertEqual(old[x:x+4],new[y:y+4])

    def test_pq_slab_preserves_mask_bytes_and_requires_extra_storage(self):
        for n in (63,257):
            data=b''.join(struct.pack('<I',i) for i in range(32*n))
            slabs=[aligned_mask_slab(data,n,j) for j in range(4)]
            self.assertEqual(b''.join(slabs),data[:4*n*4])
            self.assertEqual(sum(map(len,slabs)),4*n*4)

    def test_degenerate_strides_are_not_descriptor_starts(self):
        self.assertEqual(span([63,1,1,1],[4,252,8064,8064],4),252)
        self.assertEqual(span([128,1,8,1],[4,4096,512,4096],4),4096)


if __name__=='__main__':unittest.main()
