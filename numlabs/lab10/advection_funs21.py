'''
Module containing advection3 and, in time advection and advection2
'''
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx
import matplotlib.colorbar as colorbar
import numpy as np

def initialize(timesteps, lab_example=False):
    ''' initialize the physical system, horizontal grid size, etc
    '''
    # below are the parameters that can be varied
    u = 20.
    domain_length = 86400*20 # so it goes around the domain once in a day
    effective_points = 500
    dx = domain_length/effective_points

    dt = 0.1 * dx/ u
    Numpoints = effective_points + 1
    shift = Numpoints * dx / 2
    c_0 = 1
    alpha = 1 / (1e4)**2
    epsilon = 0.0001

    if lab_example:
        Numpoints = 77
        shift = 7
        alpha = 0.1
        dt = 0.9

# create the concentration matrix and initialize it
    cmatrix = np.zeros((timesteps+1, Numpoints+4))
    cmatrix[0, 2:Numpoints+2]= c_0 * np.exp(- alpha * (np.arange(0,Numpoints)* dx -shift)**2)

# set the boundary points
    cmatrix = boundary_conditions(cmatrix, 0, Numpoints)

    return dx, u, dt, Numpoints, shift, c_0, alpha, epsilon, cmatrix

def boundary_conditions(cmatrix, time, Numpoints):
    '''Set boundary conditions (double thick so it work for Bott Scheme as well as central and upstream
    '''
    cmatrix[time, 0] = cmatrix[time, Numpoints-1]
    cmatrix[time, 1] = cmatrix[time, Numpoints]
    cmatrix[time, Numpoints+2] = cmatrix[time, 3]
    cmatrix[time, Numpoints+3] = cmatrix[time, 4]

    return cmatrix

def advect3_gettable(order, Numpoints):

    '''read in the corresponding coefficient table for the calculation of coefficients for advection3
    '''

# create a matrix to store the table to be read in
    temp = np.zeros(5)
    ltable = np.zeros((order + 1, 5))

    fname = '../../numlabs/lab10/Tables/l{0}_table.txt'.format(order)
    fp = open(fname, 'r')

    for i in range(order+1):
        line = fp.readline()
        temp = line.split()
        ltable[i, :]= temp

    fp.close()
    return ltable

def step_advect(timesteps, cmatrix, Numpoints, u, dt, dx):
    '''Step algorithm for the Central Scheme'''
    for timecount in range(0, timesteps):

        cmatrix[timecount+1, 1:Numpoints-1]= cmatrix[timecount, 1:Numpoints-1] - (
            u * dt/(2* dx) * (cmatrix[timecount, 2:Numpoints] - cmatrix[timecount, :Numpoints-2]))

        cmatrix = boundary_conditions(cmatrix, timecount+1, Numpoints)
    return cmatrix

def step_advect2(timesteps, cmatrix, Numpoints, u, dt, dx):
    '''Step algorithm for Upstream Scheme'''

    for timecount in range(0, timesteps):

        cmatrix[timecount+1, 1:Numpoints]= cmatrix[timecount, 1:Numpoints] - (
            u * dt/ dx * (cmatrix[timecount, 1:Numpoints] - cmatrix[timecount, :Numpoints-1]))

        cmatrix = boundary_conditions(cmatrix, timecount+1, Numpoints)
    return cmatrix


def step_advect3(timesteps, ltable, cmatrix, order, Numpoints, u, dt, dx, epsilon):
    '''Step algorithm for Bott Scheme'''

# create a matrix to store the current coefficients a(j, k)
    amatrix = np.zeros((order+1, Numpoints))

    for timecount in range(0,timesteps):
        for base in range(0,5):
            amatrix[0:order+1, 0:Numpoints] += np.dot(
                ltable[0:order+2, base:base+1],
                cmatrix[timecount:timecount+1, 0+base:Numpoints+base])

# calculate I of c at j+1/2 , as well as I at j
# as these values will be needed to calculate i at j+1/2 , as
# well as i at j

# calculate I of c at j+1/2(Iplus),
# and at j(Iatj)
        Iplus = np.zeros(Numpoints)
        Iatj = np.zeros(Numpoints)

        tempvalue= 1 - 2*u*dt/dx
        for k in range(order+1):
            Iplus += amatrix[k] * (1- (tempvalue**(k+1)))/(k+1)/(2**(k+1))
            Iatj += amatrix[k] * ((-1)**k+1)/(k+1)/(2**(k+1))
        Iplus[Iplus < 0] = 0
        Iatj = np.maximum(Iatj, Iplus + epsilon)

# finally, calculate the current concentration
        cmatrix[timecount+1, 3:Numpoints+2] = (
            cmatrix[timecount, 3:Numpoints+2] *
            (1 - Iplus[1:Numpoints]/ Iatj[1:Numpoints]) +
             cmatrix[timecount, 2:Numpoints+1]*
             Iplus[0:Numpoints-1]/ Iatj[0:Numpoints-1])

# set the boundary condition at the first point
        cmatrix[timecount+1, 2]= cmatrix[timecount+1, Numpoints+1]
# set the other boundary points
        cmatrix = boundary_conditions(cmatrix, timecount+1, Numpoints)

    return cmatrix

def make_graph(ax,cmatrix, timesteps, Numpoints, dt,order):
    """Create graphs of the model results using matplotlib.
    """

    # Set the figure title, and the axes labels.
    the_title = ax.text(0.25, np.max(cmatrix)-0.05, 'Concentrations Results from t = %.3fs to %.3fs calculated with order %.1f' % (0, dt*timesteps,order) )
    ax.set_ylabel('Concentration')
    ax.set_xlabel('Grid Point')

    # We use color to differentiate lines at different times.  Set up the color map
    cmap = plt.get_cmap('copper_r')
    cNorm  = colors.Normalize(vmin=0, vmax=1.*timesteps)
    cNorm_inseconds = colors.Normalize(vmin=0, vmax=1.*timesteps*dt)
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cmap)

    # Only try to plot 20 lines, so choose an interval if more than that (i.e. plot every interval lines)
    plotsteps = (np.arange(0, timesteps, timesteps/20) + timesteps/20).astype(int)

    ax.plot(cmatrix[0, :], color='r', linewidth=3)
    # Do the main plot
    for time in plotsteps:
        colorVal = scalarMap.to_rgba(time)
        ax.plot(cmatrix[time, :], color=colorVal)

    # Add the custom colorbar
    #ax2 = ax.add_axes([0.95, 0.05, 0.05, 0.9])
    #cb1 = colorbar.ColorbarBase(ax2, cmap=cmap, norm=cNorm_inseconds)
    #cb1.set_label('Time (s)')
    return

def advection(timesteps, lab_example=True):
    '''Entry point for the Central Scheme'''
    dx, u, dt, Numpoints, shift, c_0, alpha, epsilon, cmatrix = initialize(timesteps, lab_example)

    cmatrix = step_advect(timesteps, cmatrix, Numpoints, u, dt, dx)
    make_graph(cmatrix, timesteps, Numpoints, dt)

def advection2(timesteps, lab_example=True):
    '''Entry point for the Upstream Scheme'''
    dx, u, dt, Numpoints, shift, c_0, alpha, epsilon, cmatrix = initialize(timesteps, lab_example)
    cmatrix = step_advect2(timesteps, cmatrix, Numpoints, u, dt, dx)
    make_graph(cmatrix, timesteps, Numpoints, dt)

def advection3(timesteps, order, axs,lab_example=True):
    ''' Entry point for the Bott Scheme'''
    dx, u, dt, Numpoints, shift, c_0, alpha, epsilon, cmatrix = initialize(timesteps, lab_example)
    ltable = advect3_gettable(order, Numpoints)
    cmatrix = step_advect3(timesteps, ltable, cmatrix, order, Numpoints, u, dt, dx, epsilon)
    make_graph(axs,cmatrix, timesteps, Numpoints, dt,order)
    return cmatrix
