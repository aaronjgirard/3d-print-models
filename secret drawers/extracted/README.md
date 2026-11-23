# Dial & Drawers puzzle box (150 mm)

Two-layer drawer box, 150 x 150 x 83 mm. Drawer A pulls out of one side, drawer B out of the
adjacent side, a flush dial sits in the top. All four side faces carry the same drawer seam and the
same recessed pull; only two of the eight panels are drawers. Each drawer cavity is about
131 x 127-132 x 29 mm (candy-bar sized).

## How it opens
1. Nothing moves when closed.
2. Turn the dial 30 deg clockwise (it stops at both ends). This lifts a peg out of a notch on drawer B.
3. B can now be pulled (first compartment). A is still locked by a pin that hangs from B's floor into A.
4. Close B and push it IN 6 mm past flush. The pin now lines up with a notch in A's rear wall.
5. Pull A (second compartment). Pulling B out never frees A; B is captive so it cannot be removed to cheat.

Reset: push B in 6 mm, push A home, bring B back to flush, turn the dial back anticlockwise.

## Plates (220 x 220 bed: it does not fit on one)
The two drawers are 137 mm wide each, so they cannot share a bed. Three plates:
1. drawer_a + lower_tube (188 mm across with 4 mm brims on the tube)
2. drawer_b + upper_tube (194 mm across)
3. dial + cap + lock_pin

Keep the standing tubes with their 150 mm side along Y (bed travel) so the bed's shaking works against
their stiff direction; the STLs are already oriented that way, so no rotation is needed in the slicer.

## Parts (7 STLs, already in print orientation, no supports)
| file | orientation | notes |
|---|---|---|
| lower_tube.stl | stands on its back wall, drawer opening up, long side along Y | brim recommended (150 tall on a 150 x 40 footprint) |
| upper_tube.stl | stands on its back wall, drawer opening up, long side along Y | brim recommended |
| drawer_a.stl | flat, open top up | |
| drawer_b.stl | flat, open top up | has the lock block and the pin boss inside |
| dial.stl | top face on the bed, peg up | |
| cap.stl | head on the bed | |
| lock_pin.stl | vertical | chamfered end goes down |

Suggested settings: 0.2 mm layers, 3 perimeters, 20 % infill, PLA or PETG. Print the two tubes
in one colour, the drawers and dial in whatever you like; the dial reads as a feature either way.

Clearances: drawers 0.5 mm per side, dial 0.3 mm, peg in its arc slot 0.3 mm, pin in its slots
0.3 mm. Press fits: cap stem 5.0 into a 4.8 hole, lock pin 6.0 into a 5.8 hole. Ream the holes
with a 4.8 / 5.8 mm drill if a fit is too tight; add a drop of CA if too loose.

## Assembly (in this order)
1. Put drawer A into the lower tube.
2. Set the upper tube on the lower tube: its 1 mm rim nests in the pocket on the lower tube's top,
   and the two pin slots must sit on the same side (they only line up one way). Glue the joint
   (CA or epoxy) and let it cure with the parts square.
3. Slide drawer B into the upper tube WITHOUT the pin, and push it fully home (flush).
4. From inside drawer B, press the lock pin down through the boss in B's floor, chamfer first,
   until its top is flush with the boss. It passes through both plate slots and ends 2.5 mm into
   drawer A's cavity, just in front of A's rear wall.
5. Drop the dial into the top recess with its peg going through the curved slot; with B closed the
   peg lands in the notch of B's lock block (dial in the locked position).
6. Press the centre cap through the dial into the ceiling hole until the head is flush.

## Design notes
- The case is two open-top trays printed on their back walls, so there are no bridges anywhere;
  the lower tube's pin slot has a 45 deg roof for the same reason.
- Only the back 2.5 mm of each drawer cavity is reduced in height by the pin or peg; everything
  else is the full 29 mm.
- B's travel is 100 mm out and 6 mm in; its back 37 mm never leaves the case.
- Source: puzzle_drawers.py (manifold3d + trimesh), render.py makes the previews.
