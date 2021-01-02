Water phantom
c Cell cards
c Water phantom
1 1 -1.0 2 -1 4 -3 5 -6 fill=1 imp:p,e 1
c Lattice call for dose deposition
10 1 -1.0 2 -1 4 -3 5 -10 lat=1 u=1 imp:p,e 1
c Air around
100 2 -0.001293 (101 -102 -100) #1 imp:p,e 1
c Void cell
999 0 -101:102:100 imp:p=0 imp:e=0

c Surface cards
c Water phantom
1 px 5
2 px -5
3 py 5
4 py -5
5 pz 10
6 pz 20
c Lattice cell
10 pz 11
c Cylinder around the problem
100 cz 9
101 pz -0.1
102 pz 25

c Data cards
mode p e
c Materials
m1 1000. 2
 8000. 1 $Water
m2 7014.
 -0.755636 $air (US S. Atm at sea level)
8016.
 -0.231475 18000.
 -0.012889
c Source cards
sdef pos=0 0 0 x=d1 y=d2 z=0 erg=10 par=2 $
si1 -6 6
sp1 0 1
si2 -6 6
sp2 0 1
c Tallies
F1:p 6
e1 1 99i 10 $ Energy spectrum, step 0.1 MV
*F8:p (10<10[0:0 0:0 -9:0]) $Depth dose tally
cut:e j 0.1 $100 keV (default is 1 keV)
cut:p j 0.01 $10 keV (default is 1 keV)
PHYS:P 4j 1 $turns off Doppler broadening
nps 1000000
