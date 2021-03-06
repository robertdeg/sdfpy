from fractions import Fraction
import math

def gcd( x, *xs ):
    try:
        it = iter( x )
        g = next( it )
        for y in it:
            g = math.gcd( g, y )
    except TypeError:
        g = x

    for y in xs:
        g = math.gcd( g, y )

    return g

def lcm(a, b):
    return a * b // math.gcd(a, b)

def modinv(a, m):
    g, x, y = xgcd(a, m)
    if g != 1:
        return None  # modular inverse does not exist
    else:
        return x % m

def xgcd(a, b):
    """ Returns triplet g, x, y such that ax + by = g = gcd(a, b)
    Taken from: http://en.wikibooks.org/wiki/Algorithm_Implementation/Mathematics/Extended_Euclidean_algorithm
    """
    x,y, u,v = 0,1, 1,0
    while a != 0:
        q, r = b//a, b%a
        m, n = x-u*q, y-v*q
        b,a, x,y, u,v = a,r, u,v, m,n
    _gcd = b
    return _gcd, x, y

def crt2( n1, a1, n2, a2 ):
    """ Computes the solution to the 2 simultaneous congruence relations:

        x = a1 (mod n1)
        x = a2 (mod n2)
    """
    g = math.gcd( n1, n2 )
    delta = a2 - a1
    if delta % g != 0:
        raise ArithmeticError("No solution")

    delta = delta // g
    inv = mul_inv( n1 // g, n2 // g )
    modulus = (n1 // g) * n2
    return modulus, (a1 + n1 * inv * delta) % modulus

def chinese_remainder(n, a):
    """ Computes the solution of a system of congruence relations, given by n and a

        n:  list of moduli
        a:  list of remainders

    """
    tups = iter(zip(n, a))
    n1, a1 = next(tups)
    for n2, a2 in tups:
        n1, a1 = crt2( n1, a1, n2, a2 )

    return n1, a1
 
def mul_inv(a, b):
    b0 = b
    x0, x1 = 0, 1
    if b == 1: return 1
    while a > 1:
        q = a // b
        a, b = b, a%b
        x0, x1 = x1 - q * x0, x0
    if x1 < 0: x1 += b0
    return x1


def max_mods(a1, b1, m1, a2, b2, m2):
    """ Computes the maximum of the sum of:
        
          (a1 + b1 * x) mod m1 + (a2 + b2 * x) mod m2,
        
        taken over all possible integer values of x
    """
    values1 = m1 // gcd( b1, m1 )
    values2 = m2 // gcd( b2, m2 )
    count = lcm( values1, values2 )
    max_v = -1, 0, 0
    arg_max = None
    for i in range(2 * count):
        v1 = (a1 + b1 * i) % m1
        v2 = (a2 + b2 * i) % m2
        v = v1 + v2
        if v > max_v[0]:
            max_v = v, v1, v2
            arg_max = i
            
    print("Max value = {}, attained at x = {}".format(max_v[0], arg_max))
    print("Value: {} + {}".format( max_v[1], max_v[2] ))
