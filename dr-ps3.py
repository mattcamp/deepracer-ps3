import requests
from bs4 import BeautifulSoup
import cv2
import numpy as np
import os
import pprint
import pygame
import json
import urllib3
import pytweening
urllib3.disable_warnings()


class PS4Controller(object):
    """Class representing the PS4 controller. Pretty straightforward functionality."""

    controller = None
    axis_data = None
    button_data = None
    hat_data = None

    def init(self):
        """Initialize the joystick components"""

        pygame.init()
        pygame.joystick.init()
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()


if __name__ == "__main__":
    ps4 = PS4Controller()
    ps4.init()
    # ps4.listen()

    with requests.Session() as s:
        URL = "https://192.168.13.4/"
        post_login_url = "https://192.168.13.4/login"
        video_url = "https://192.168.13.4/route?topic=/video_mjpeg&width=480&height=360"
        drivemode_url = URL+"api/drive_mode"
        startstop_url = URL+"api/start_stop"
        manual_url = "https://192.168.13.4/api/manual_drive"
        home_url = "https://192.168.13.4/home"

        # Get the CSRF Token
        response = s.get(URL, verify=False)

        soup = BeautifulSoup(response.text, 'lxml')
        csrf_token = soup.select_one('meta[name="csrf-token"]')['content']
        headers = {'X-CSRFToken': csrf_token}
        # print("CSRF token found: " + str(csrf_token))

        # Login to the DeepRacer web interface with Post
        payload = {'password': '<password>'}
        post = s.post(post_login_url, data=payload, headers=headers, verify=False)

        body_data = {'drive_mode': "manual"}
        req = s.post(drivemode_url, json=body_data, headers=headers, verify=False)

        body_data = {'start_stop': 'start'}
        req = s.post(startstop_url, json=body_data, headers=headers, verify=False)

        # Get the video stream
        video_stream = s.get(video_url, stream=True, verify=False)
        if video_stream.status_code == 200:
            print("Video Connected!")
            steering_angle = 0.0
            throttle = 0.0

            bytes = bytes()
            for chunk in video_stream.iter_content(chunk_size=1024):
                bytes += chunk
                a = bytes.find(b'\xff\xd8')  # Marker byte pair
                b = bytes.find(b'\xff\xd9')  # Trailing byte pair
                #  If both byte pairs on in the stream then build the jpeg
                if a != -1 and b != -1:
                    jpg = bytes[a:b + 2]
                    bytes = bytes[b + 2:]
                    i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    cv2.imshow('Raw Image', i)

                    for event in pygame.event.get():
                        if event.type == pygame.JOYAXISMOTION:

                            if event.axis == 0:

                                if event.value < 0:
                                    tmp = round(event.value, 2)*-1
                                    if tmp > 1.0:
                                        tmp = 1.0

                                    steering_angle = (pytweening.easeInQuad(tmp))*-1
                                else:
                                    tmp = round(event.value, 2)
                                    if tmp > 1.0:
                                        tmp = 1.0
                                    steering_angle = pytweening.easeInQuad(tmp)

                            if event.axis == 3:
                                if event.value < 0:
                                    tmp = round(event.value, 2)*-1
                                    if tmp > 1.0:
                                        tmp = 1.0
                                    throttle = (pytweening.easeInQuad(tmp))*-1
                                else:
                                    tmp = round(event.value, 2)
                                    if tmp > 1.0:
                                        tmp = 1.0
                                    throttle = pytweening.easeInQuad(tmp)

                            body_data = { "angle": steering_angle, "throttle": throttle }
                            print(body_data)
                            req = s.post(manual_url, headers=headers, json=body_data, verify=False)

                    if cv2.waitKey(1) == 27:
                        exit(0)
        else:
            print("Received unexpected status code {}".format(video_stream.status_code))