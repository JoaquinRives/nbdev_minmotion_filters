# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_ahrs_madwick_mahony.ipynb (unless otherwise specified).

__all__ = ['Quaternion', 'MadgwickAHRS', 'MahonyAHRS']

# Cell
import numpy as np
from numpy.linalg import norm
import numbers
import warnings

# Cell
class Quaternion:
    """
    A simple class implementing basic quaternion arithmetic.
    """
    def __init__(self, w_or_q, x=None, y=None, z=None):
        """
        Initializes a Quaternion object
        :param w_or_q: A scalar representing the real part of the quaternion, another Quaternion object or a
                    four-element array containing the quaternion values
        :param x: The first imaginary part if w_or_q is a scalar
        :param y: The second imaginary part if w_or_q is a scalar
        :param z: The third imaginary part if w_or_q is a scalar
        """
        self._q = np.array([1, 0, 0, 0])

        if x is not None and y is not None and z is not None:
            w = w_or_q
            q = np.array([w, x, y, z])
        elif isinstance(w_or_q, Quaternion):
            q = np.array(w_or_q.q)
        else:
            q = np.array(w_or_q)
            if len(q) != 4:
                raise ValueError("Expecting a 4-element array or w x y z as parameters")

        self._set_q(q)

    # Quaternion specific interfaces

    def conj(self):
        """
        Returns the conjugate of the quaternion
        :rtype : Quaternion
        :return: the conjugate of the quaternion
        """
        return Quaternion(self._q[0], -self._q[1], -self._q[2], -self._q[3])

    def to_angle_axis(self):
        """
        Returns the quaternion's rotation represented by an Euler angle and axis.
        If the quaternion is the identity quaternion (1, 0, 0, 0), a rotation along the x axis with angle 0 is returned.
        :return: rad, x, y, z
        """
        if self[0] == 1 and self[1] == 0 and self[2] == 0 and self[3] == 0:
            return 0, 1, 0, 0
        rad = np.arccos(self[0]) * 2
        imaginary_factor = np.sin(rad / 2)
        if abs(imaginary_factor) < 1e-8:
            return 0, 1, 0, 0
        x = self._q[1] / imaginary_factor
        y = self._q[2] / imaginary_factor
        z = self._q[3] / imaginary_factor
        return rad, x, y, z

    def quatern2rotMat(self):
        #Converts a quaternion orientation to a rotation matrix
        R = np.zeros((3,3))

        #Original Matlab Code:
        #R(1,1,:) = 2.*q(:,1).^2-1+2.*q(:,2).^2;
        #R(1,2,:) = 2.*(q(:,2).*q(:,3)+q(:,1).*q(:,4));
        #R(1,3,:) = 2.*(q(:,2).*q(:,4)-q(:,1).*q(:,3));

        R[0,0] = 2. * self._q[0] ** 2 - 1. + 2. * self._q[1] ** 2
        R[0,1] = 2. * (self._q[1] * self._q[2] + self._q[0] * self._q[3])
        R[0,2] = 2. * (self._q[1] * self._q[3] - self._q[0] * self._q[2])

        #R(2,1,:) = 2.*(q(:,2).*q(:,3)-q(:,1).*q(:,4));
        #R(2,2,:) = 2.*q(:,1).^2-1+2.*q(:,3).^2;
        #R(2,3,:) = 2.*(q(:,3).*q(:,4)+q(:,1).*q(:,2));

        R[1,0] = 2. * (self._q[1] * self._q[2] - self._q[0] * self._q[3])
        R[1,1] = 2. * self._q[0] ** 2 - 1. + 2. * self._q[2] ** 2
        R[1,2] = 2. * (self._q[2] * self._q[3] + self._q[0] * self._q[1])

        #R(3,1,:) = 2.*(q(:,2).*q(:,4)+q(:,1).*q(:,3));
        #R(3,2,:) = 2.*(q(:,3).*q(:,4)-q(:,1).*q(:,2));
        #R(3,3,:) = 2.*q(:,1).^2-1+2.*q(:,4).^2;

        R[2,0] = 2. * (self._q[1] * self._q[3] + self._q[0] * self._q[2])
        R[2,1] = 2. * (self._q[2] * self._q[3] - self._q[0] * self._q[1])
        R[2,2] = 2. * self._q[0] ** 2 - 1. + 2. * self._q[3] ** 2

        return R

    @staticmethod
    def from_angle_axis(rad, x, y, z):
        s = np.sin(rad / 2)
        return Quaternion(np.cos(rad / 2), x*s, y*s, z*s)

    def to_euler_angles(self):
        pitch = np.arcsin(2 * self[1] * self[2] + 2 * self[0] * self[3])
        if np.abs(self[1] * self[2] + self[3] * self[0] - 0.5) < 1e-8:
            roll = 0
            yaw = 2 * np.arctan2(self[1], self[0])
        elif np.abs(self[1] * self[2] + self[3] * self[0] + 0.5) < 1e-8:
            roll = -2 * np.arctan2(self[1], self[0])
            yaw = 0
        else:
            roll = np.arctan2(2 * self[0] * self[1] - 2 * self[2] * self[3], 1 - 2 * self[1] ** 2 - 2 * self[3] ** 2)
            yaw = np.arctan2(2 * self[0] * self[2] - 2 * self[1] * self[3], 1 - 2 * self[2] ** 2 - 2 * self[3] ** 2)
        return roll, pitch, yaw

    def to_euler123(self):
        roll = np.arctan2(-2*(self[2]*self[3] - self[0]*self[1]), self[0]**2 - self[1]**2 - self[2]**2 + self[3]**2)
        pitch = np.arcsin(2*(self[1]*self[3] + self[0]*self[1]))
        yaw = np.arctan2(-2*(self[1]*self[2] - self[0]*self[3]), self[0]**2 + self[1]**2 - self[2]**2 - self[3]**2)
        return roll, pitch, yaw

    def __mul__(self, other):
        """
        multiply the given quaternion with another quaternion or a scalar
        :param other: a Quaternion object or a number
        :return:
        """
        if isinstance(other, Quaternion):
            w = self._q[0]*other._q[0] - self._q[1]*other._q[1] - self._q[2]*other._q[2] - self._q[3]*other._q[3]
            x = self._q[0]*other._q[1] + self._q[1]*other._q[0] + self._q[2]*other._q[3] - self._q[3]*other._q[2]
            y = self._q[0]*other._q[2] - self._q[1]*other._q[3] + self._q[2]*other._q[0] + self._q[3]*other._q[1]
            z = self._q[0]*other._q[3] + self._q[1]*other._q[2] - self._q[2]*other._q[1] + self._q[3]*other._q[0]

            return Quaternion(w, x, y, z)
        elif isinstance(other, numbers.Number):
            q = self._q * other
            return Quaternion(q)

    def __add__(self, other):
        """
        add two quaternions element-wise or add a scalar to each element of the quaternion
        :param other:
        :return:
        """
        if not isinstance(other, Quaternion):
            if len(other) != 4:
                raise TypeError("Quaternions must be added to other quaternions or a 4-element array")
            q = self.q + other
        else:
            q = self.q + other.q

        return Quaternion(q)

    # Implementing other interfaces to ease working with the class

    def _set_q(self, q):
        self._q = q

    def _get_q(self):
        return self._q

    q = property(_get_q, _set_q)

    def __getitem__(self, item):
        return self._q[item]

    def __array__(self):
        return self._q

# Cell
class MadgwickAHRS:
    samplePeriod = 1/256
    quaternion = Quaternion(1, 0, 0, 0)
    beta = 1

    def __init__(self, sampleperiod=None, quaternion=None, beta=None):
        """
        Initialize the class with the given parameters.
        :param sampleperiod: The sample period
        :param quaternion: Initial quaternion
        :param beta: Algorithm gain beta
        :return:
        """
        if sampleperiod is not None:
            self.samplePeriod = sampleperiod
        if quaternion is not None:
            self.quaternion = quaternion
        if beta is not None:
            self.beta = beta

    def update(self, gyroscope, accelerometer, magnetometer):
        """
        Perform one update step with data from a AHRS sensor array
        :param gyroscope: A three-element array containing the gyroscope data in radians per second.
        :param accelerometer: A three-element array containing the accelerometer data. Can be any unit since a normalized value is used.
        :param magnetometer: A three-element array containing the magnetometer data. Can be any unit since a normalized value is used.
        :return:
        """
        q = self.quaternion

        gyroscope = np.array(gyroscope, dtype=float).flatten()
        accelerometer = np.array(accelerometer, dtype=float).flatten()
        magnetometer = np.array(magnetometer, dtype=float).flatten()

        # Normalise accelerometer measurement
        if norm(accelerometer) is 0:
            warnings.warn("accelerometer is zero")
            return
        accelerometer /= norm(accelerometer)

        # Normalise magnetometer measurement
        if norm(magnetometer) is 0:
            warnings.warn("magnetometer is zero")
            return
        magnetometer /= norm(magnetometer)

        h = q * (Quaternion(0, magnetometer[0], magnetometer[1], magnetometer[2]) * q.conj())
        b = np.array([0, norm(h[1:3]), 0, h[3]])

        # Gradient descent algorithm corrective step
        f = np.array([
            2*(q[1]*q[3] - q[0]*q[2]) - accelerometer[0],
            2*(q[0]*q[1] + q[2]*q[3]) - accelerometer[1],
            2*(0.5 - q[1]**2 - q[2]**2) - accelerometer[2],
            2*b[1]*(0.5 - q[2]**2 - q[3]**2) + 2*b[3]*(q[1]*q[3] - q[0]*q[2]) - magnetometer[0],
            2*b[1]*(q[1]*q[2] - q[0]*q[3]) + 2*b[3]*(q[0]*q[1] + q[2]*q[3]) - magnetometer[1],
            2*b[1]*(q[0]*q[2] + q[1]*q[3]) + 2*b[3]*(0.5 - q[1]**2 - q[2]**2) - magnetometer[2]
        ])
        j = np.array([
            [-2*q[2],                  2*q[3],                  -2*q[0],                  2*q[1]],
            [2*q[1],                   2*q[0],                  2*q[3],                   2*q[2]],
            [0,                        -4*q[1],                 -4*q[2],                  0],
            [-2*b[3]*q[2],             2*b[3]*q[3],             -4*b[1]*q[2]-2*b[3]*q[0], -4*b[1]*q[3]+2*b[3]*q[1]],
            [-2*b[1]*q[3]+2*b[3]*q[1], 2*b[1]*q[2]+2*b[3]*q[0], 2*b[1]*q[1]+2*b[3]*q[3],  -2*b[1]*q[0]+2*b[3]*q[2]],
            [2*b[1]*q[2],              2*b[1]*q[3]-4*b[3]*q[1], 2*b[1]*q[0]-4*b[3]*q[2],  2*b[1]*q[1]]
        ])
        step = j.T.dot(f)
        step /= norm(step)  # normalise step magnitude

        # Compute rate of change of quaternion
        qdot = (q * Quaternion(0, gyroscope[0], gyroscope[1], gyroscope[2])) * 0.5 - self.beta * step.T

        # Integrate to yield quaternion
        q += qdot * self.samplePeriod
        self.quaternion = Quaternion(q / norm(q))  # normalise quaternion

    def update_imu(self, gyroscope, accelerometer):
        """
        Perform one update step with data from a IMU sensor array
        :param gyroscope: A three-element array containing the gyroscope data in radians per second.
        :param accelerometer: A three-element array containing the accelerometer data. Can be any unit since a normalized value is used.
        """
        q = self.quaternion

        #gyroscope = np.array(gyroscope, dtype=float).flatten()
        #accelerometer = np.array(accelerometer, dtype=float).flatten()

        # Normalise accelerometer measurement
        if norm(accelerometer) is 0:
            warnings.warn("accelerometer is zero")
            return
        accelerometer /= norm(accelerometer)

        # Gradient descent algorithm corrective step
        f = np.array([
            2*(q[1]*q[3] - q[0]*q[2]) - accelerometer[0],
            2*(q[0]*q[1] + q[2]*q[3]) - accelerometer[1],
            2*(0.5 - q[1]**2 - q[2]**2) - accelerometer[2]
        ])
        j = np.array([
            [-2*q[2], 2*q[3], -2*q[0], 2*q[1]],
            [2*q[1], 2*q[0], 2*q[3], 2*q[2]],
            [0, -4*q[1], -4*q[2], 0]
        ])
        step = j.T.dot(f)
        step /= norm(step)  # normalise step magnitude

        # Compute rate of change of quaternion
        qdot = (q * Quaternion(0, gyroscope[0], gyroscope[1], gyroscope[2])) * 0.5 - self.beta * step.T

        # Integrate to yield quaternion
        q += qdot * self.samplePeriod
        self.quaternion = Quaternion(q / norm(q))  # normalise quaternion

# Cell

class MahonyAHRS:
    def __init__(self, sampleperiod=None, quaternion=None, Kp=None, Ki=None):
        self.samplePeriod = 1. / 256.
        self.quaternion = Quaternion(1., 0., 0., 0.) #output quaternion describing the Earth relative to the sensor
        self.Kp = 1.                                 #algorithm proportional gain
        self.Ki = 0.                                 #algorithm integral gain
        self.eInt = np.zeros(3)                      #integral error

        if sampleperiod is not None:
            self.samplePeriod = sampleperiod
        if quaternion is not None:
            self.quaternion = quaternion
        if Kp is not None:
            self.Kp = Kp
        if Ki is not None:
            self.Ki = Ki



    def update_imu(self, gyr, acc):
        """
        Perform one update step with data from a IMU sensor array
        :param gyroscope: A three-element array containing the gyroscope data in radians per second.
        :param accelerometer: A three-element array containing the accelerometer data. Can be any unit since a normalized value is used.
        """

        gyroscope = gyr.copy()
        accelerometer = acc.copy()

        q = (self.quaternion._q).copy()  # TODO: debug [1, 0, 0, 0]

        # gyroscope = np.array(gyroscope, dtype=float).flatten()
        # accelerometer = np.array(accelerometer, dtype=float).flatten()

        # Normalise accelerometer measurement
        accnorm = np.linalg.norm(accelerometer)
        if(accnorm > 0.):
            accelerometer /= accnorm

        # Estimated direction of gravity and magnetic flux
        v = np.array([2. * (q[1]*q[3] - q[0]*q[2]),2. * (q[0]*q[1] + q[2]*q[3]),q[0] ** 2 - q[1] ** 2 - q[2] ** 2 + q[3] ** 2])

        # Error is sum of cross product between estimated direction and measured direction of field

        e = np.cross(accelerometer, v, axisa=0)  # TODO - Before: e = np.cross(accelerometer, v)
        if(self.Ki > 0.):
            self.eInt += e * self.samplePeriod # Error is sum of cross product between estimated direction and measured direction of field
        else:
            self.eInt = np.zeros(3)

        gyroscope111 = gyroscope.copy()
        gyroscope222 = gyroscope.T.copy()
        gyroscope333 = gyroscope.T.copy()

        #Apply feedback terms
        gyroscope += (self.Kp * e + self.Ki * self.eInt)  # TODO - Before: gyroscope += self.Kp * e + self.Ki * self.eInt)

        #Compute rate of change of quaternion
        qDot = self.quaternion * Quaternion(0.,0.5 * gyroscope[0],0.5 * gyroscope[1],0.5 * gyroscope[2])
        qDot = qDot._q


        #Integrate to yield quaternion
        q += qDot * self.samplePeriod
        q /= np.linalg.norm(q) #normalise quaternion

        self.quaternion._q = q.copy() #copy back