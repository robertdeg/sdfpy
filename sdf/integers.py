from fractions import gcd

def lcm(a, b):
    return a * b // gcd(a, b)

def xgcd_old(a,b):
    a1 = 1; b1 = 0; a2 = 0; b2 = 1
    while (1):
        quot = -(a // b)
        a = a % b
        a1 = a1 + quot*a2; b1 = b1 + quot*b2
        if(a == 0):
            return [b, a2, b2]
        quot = -(b // a)
        b = b % a;
        a2 = a2 + quot*a1; b2 = b2 + quot*b1
        if(b == 0):
            return [a, a1, b1]

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
