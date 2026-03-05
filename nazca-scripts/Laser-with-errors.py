import nazca as nd
import nazca.demofab as demo

def dbr_laser(Ldbr1=50, Ldbr2=500, Lsoa=750, Lpm=70):
    """Create a parametrized dbr laser building block."""
    with nd.Cell(name='laser') as laser:
        #create an isolation cell for reuse
        iso = demo.isolation_act(length=20)

        #draw the laser
        s2a   = demo.s2a().put(0)
        dbr1  = demo.dbr(length=Ldbr1).put()
        iso.put()
        soa   = demo.soa(length=Lsoa).put()
        iso.put()
        phase = demo.phase_shifter(length=Lpm).put()
        iso.put()
        dbr2  = demo.dbr(length=Ldbr2).put()
        a2s   = demo.a2s().put()

        # add pins to the laser building block
        nd.Pin('a0', pin=s2a.pin['a0']).put()
        nd.Pin('b0', pin=a2s.pin['b0']).put()
        nd.Pin('c0', pin=dbr1.pin['c0']).put()
        nd.Pin('c1', pin=soa.pin['c0']).put()
        nd.Pin('c2', pin=phase.pin['c0']).put()
        nd.Pin('c3', pin=dbr2.pin['c0']).put()
    return laser

#place several lasers:
laser1 = dbr_laser(Lsoa=750).put(0)
laser2 = dbr_laser(Lsoa=1000).put(0, -200)  # small offset -> overlap
laser3 = dbr_laser(Lsoa=500, Ldbr1=20, Ldbr2=800, Lpm=150).put(0, -600)

demo.shallow.bend(angle=-45).put(laser1.pin['b0'])

nd.export_gds(filename="laser_with_errors.gds")