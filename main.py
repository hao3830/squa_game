import os
import cv2
import pygame
import time
import numpy as np
import mediapipe as mp

from models.pose_landmarker import PoseLandmarker

pygame.init()

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 640, 800
PLAY_BUTTON_SIZE = 120
BLUR_RADIUS = 15
RULE_WIDTH = WINDOW_WIDTH * 2 // 3
RULE_HEIGHT = 150
PADDING = WINDOW_HEIGHT // 30
GAME_NAME_WIDTH = WINDOW_HEIGHT * 3 // 5
GAME_NAME_HEIGHT = WINDOW_HEIGHT * 2 // 5
POPUP_WIDTH, POPUP_HEIGHT = 300, 350
BUTTON_WIDTH, BUTTON_HEIGHT = 80, 80
BUTTON_MARGIN = 100
COUNT_DOWN_WIDTH = 180
COUNT_DOWN_HEIGHT = 70

RESOURCE = "resource"

ROI_X, ROI_Y, ROI_W, ROI_H = (
    WINDOW_WIDTH // 5,
    WINDOW_HEIGHT // 8,
    WINDOW_WIDTH * 3 // 5,
    WINDOW_HEIGHT * 8 // 10,
)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("SQUAT GAME")
        self.clock = pygame.time.Clock()
        self.is_playing = False
        self.camera = cv2.VideoCapture(0)
        self.show_settings_popup = False

        # Load the play button image
        self.play_button_image = pygame.image.load(
            os.path.join(RESOURCE, "play_button.png")
        )
        self.play_button_image = pygame.transform.scale(
            self.play_button_image, (PLAY_BUTTON_SIZE, PLAY_BUTTON_SIZE)
        )

        # Load the transparent image to be displayed below the button
        self.transparent_image = pygame.image.load(os.path.join(RESOURCE, "rule.png"))
        self.transparent_image = pygame.transform.scale(
            self.transparent_image, (RULE_WIDTH, RULE_HEIGHT)
        )

        # Load transparent settings button
        self.settings_button_image = pygame.image.load(
            os.path.join(RESOURCE, "settings_button.png")
        )
        self.settings_button_image = pygame.transform.scale(
            self.settings_button_image,
            (PLAY_BUTTON_SIZE * 3 // 4, PLAY_BUTTON_SIZE * 3 // 4),
        )

        self.game_name = pygame.image.load(os.path.join(RESOURCE, "squat_game.png"))
        self.game_name = pygame.transform.scale(
            self.game_name, (GAME_NAME_WIDTH, GAME_NAME_HEIGHT)
        )

        self.reset_btn_image = pygame.image.load(os.path.join(RESOURCE, "reset.png"))
        self.reset_btn_image = pygame.transform.scale(
            self.reset_btn_image,
            (PLAY_BUTTON_SIZE // 2, PLAY_BUTTON_SIZE // 2),
        )

        self.button_rect = None
        self.dev_mode_able = False
        self.time_count = 60
        self.current_time_count = None
        self.start_time_count = None
        self.time_count_btn_minus = None
        self.time_count_btn_plus = None

        self.goal_count = 10
        self.current_count = self.goal_count
        self.goal_count_btn_minus = None
        self.goal_count_btn_plus = None

        self.settings_surface = None
        self.current_start_time = 3
        self.current_clock = 0
        self.pose_landmarker = PoseLandmarker()
        self.start_signal = False
        self.start_signal_time = None
        self.is_validated = False
        self.current_status = "STANDING"
        self.replay_btn = None
        self.is_open_gift = False
        self.open_btn = None

    def display_count_down(self):
        popup_x = PADDING // 4 + PLAY_BUTTON_SIZE // 2 + 20
        popup_y = PADDING // 4
        self.count_down_surface = pygame.Surface(
            (COUNT_DOWN_WIDTH, PLAY_BUTTON_SIZE // 2),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            self.count_down_surface,
            (0, 0, 0, 128),
            (0, 0, COUNT_DOWN_WIDTH, PLAY_BUTTON_SIZE // 2),
            border_radius=10,
        )

        self.timer = pygame.image.load(os.path.join(RESOURCE, "timer-flash-line.png"))
        self.timer = pygame.transform.scale(
            self.timer, (COUNT_DOWN_WIDTH // 4, PLAY_BUTTON_SIZE // 2 * 3 // 4)
        )

        self.count_down_surface.blit(
            self.timer, (COUNT_DOWN_WIDTH // 10, PLAY_BUTTON_SIZE // 2 // 4 // 2)
        )

        # self.time_text =
        bold_font = pygame.font.Font(os.path.join(RESOURCE, "Baloo2-Bold.ttf"), 30)
        if self.start_signal and self.start_time_count is not None:
            self.current_time_count = time.time()
            minute = max(
                int((self.time_count - self.current_time_count + self.start_time_count))
                // 60,
                0,
            )
            second = max(
                int((self.time_count - self.current_time_count + self.start_time_count))
                % 60,
                0,
            )
            self.current_clock = (
                self.time_count - self.current_time_count + self.start_time_count
            )
        else:
            minute = self.time_count // 60
            second = self.time_count % 60

        time_text = bold_font.render(
            f"{minute:02d}:{second:02d}", True, (255, 255, 255)
        )

        self.count_down_surface.blit(
            time_text,
            (
                COUNT_DOWN_WIDTH // 10 + COUNT_DOWN_WIDTH // 4 + COUNT_DOWN_WIDTH // 10,
                PLAY_BUTTON_SIZE // 2 // 4 // 2,
            ),
        )
        self.screen.blit(self.count_down_surface, (popup_x, popup_y))

        squat_icon = pygame.image.load(os.path.join(RESOURCE, "squat_icon.png"))
        squat_icon = pygame.transform.scale(
            squat_icon, (PLAY_BUTTON_SIZE * 3 // 4, PLAY_BUTTON_SIZE * 3 // 4)
        )

        self.screen.blit(
            squat_icon, (WINDOW_WIDTH // 2 + popup_x, PLAY_BUTTON_SIZE // 2 // 4 // 2)
        )

        # create blue surface
        self.blue_surface = pygame.Surface(
            (PLAY_BUTTON_SIZE * 3 // 4, PLAY_BUTTON_SIZE * 3 // 4),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            self.blue_surface,
            (0, 205, 192, 128),
            (0, 0, PLAY_BUTTON_SIZE * 3 // 4, PLAY_BUTTON_SIZE * 3 // 4),
            border_radius=10,
        )
        bold_font_2 = pygame.font.Font(os.path.join(RESOURCE, "Baloo2-Bold.ttf"), 70)
        # draw count text in center of surface
        count_text = bold_font_2.render(
            f"{self.current_count:02d}", True, (255, 255, 255)
        )
        self.blue_surface.blit(count_text, (PLAY_BUTTON_SIZE // 4 // 4 + 5, -10))

        self.screen.blit(
            self.blue_surface,
            (WINDOW_WIDTH - PLAY_BUTTON_SIZE, PLAY_BUTTON_SIZE // 2 // 4 // 2),
        )

    def display_roi(self):
        popup_x = ROI_X
        popup_y = ROI_Y
        self.roi_surface = pygame.image.load(os.path.join(RESOURCE, "roi.png"))
        self.roi_surface = pygame.transform.scale(self.roi_surface, (ROI_W, ROI_H))
        # add image in center of roi
        count_down_background = pygame.image.load(
            os.path.join(RESOURCE, "center_countdown.png")
        )
        count_down_background = pygame.transform.scale(
            count_down_background, (WINDOW_WIDTH // 4, WINDOW_WIDTH // 4)
        )
        # add text in center of count_down_background
        bold_font = pygame.font.Font(os.path.join(RESOURCE, "Baloo2-Bold.ttf"), 70)
        text = None
        if (
            self.start_signal
            and self.is_validated
            and self.start_signal_time is not None
        ):
            current_time = int(
                self.current_start_time - (time.time() - self.start_signal_time)
            )
            # print(current_time)
            if current_time > 0:
                text = bold_font.render(f"0{current_time}", True, (0, 0, 0))
            elif current_time == 0:
                text = bold_font.render("GO", True, (0, 0, 0))
            elif self.start_time_count is None:
                current_time = 3
                self.start_time_count = time.time()
        else:
            text = bold_font.render(f"0{self.current_start_time}", True, (0, 0, 0))
        if text is not None:
            count_down_background.blit(
                text, (WINDOW_WIDTH // 4 // 2 - 40, WINDOW_WIDTH // 4 // 2 // 2 - 10)
            )

            self.roi_surface.blit(
                count_down_background,
                (
                    ROI_W // 2 - WINDOW_WIDTH // 4 // 2,
                    ROI_H // 2 - WINDOW_WIDTH // 4 // 2,
                ),
            )

            # add a text below the image
            bold_font = pygame.font.Font(os.path.join(RESOURCE, "Baloo2-Bold.ttf"), 18)
            text = bold_font.render(
                "Vui lòng đứng vào chính giữa", True, (255, 255, 255)
            )
            self.screen.blit(text, (popup_x + 80, popup_y + ROI_H + PADDING // 3))
            text = bold_font.render(
                " khung hình để bắt đầu chơi ", True, (255, 255, 255)
            )
            self.screen.blit(text, (popup_x + 80, popup_y + ROI_H + PADDING))
        self.screen.blit(self.roi_surface, (popup_x, popup_y))

    def display_settings_popup(self):
        background = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        background.fill((0, 0, 0, 128))
        self.screen.blit(background, (0, 0))

        popup_x = (WINDOW_WIDTH - POPUP_WIDTH) // 2
        popup_y = (WINDOW_HEIGHT - POPUP_HEIGHT) // 2

        btn_disable_image = pygame.image.load(os.path.join(RESOURCE, "btn_disable.png"))
        btn_disable_image = pygame.transform.scale(
            btn_disable_image, (BUTTON_WIDTH, BUTTON_HEIGHT)
        )

        btn_able_image = pygame.image.load(os.path.join(RESOURCE, "btn_able.png"))
        btn_able_image = pygame.transform.scale(
            btn_able_image, (BUTTON_WIDTH, BUTTON_HEIGHT)
        )

        btn_minus = pygame.image.load(os.path.join(RESOURCE, "minus.png"))
        btn_minus = pygame.transform.scale(
            btn_minus, (BUTTON_WIDTH // 3, BUTTON_HEIGHT // 3)
        )

        btn_plus = pygame.image.load(os.path.join(RESOURCE, "plus.png"))
        btn_plus = pygame.transform.scale(
            btn_plus, (BUTTON_WIDTH // 3, BUTTON_HEIGHT // 3)
        )

        settings_surface = pygame.Surface((POPUP_WIDTH, POPUP_HEIGHT), pygame.SRCALPHA)
        self.settings_surface = pygame.Rect(popup_x, popup_y, POPUP_WIDTH, POPUP_HEIGHT)
        # Add the dashed border rectangle
        border_rect = pygame.Rect(0, 0, POPUP_WIDTH - 10, POPUP_HEIGHT - 10)
        border_rect.inflate_ip(
            -10, -10
        )  # To create an inner rectangle with a border effect
        pygame.draw.rect(
            settings_surface, (255, 255, 255, 255), border_rect, border_radius=10
        )

        # Add the headers
        font = pygame.font.Font(
            os.path.join(RESOURCE, "Baloo2-VariableFont_wght.ttf"), 16
        )
        bold_font = pygame.font.Font(os.path.join(RESOURCE, "Baloo2-Bold.ttf"), 24)
        header1 = bold_font.render("Tùy chỉnh", True, (0, 0, 0))
        header2 = bold_font.render("Dev mode", True, (0, 0, 0))
        # Add the text
        time_settings = font.render("Thời gian (giây)", True, (0, 0, 0))
        number_squat = font.render("Số lần Squats", True, (0, 0, 0))
        x = POPUP_WIDTH // 7
        # Center the text below the headers
        text1_rect = time_settings.get_rect(
            center=(POPUP_WIDTH // 4, POPUP_HEIGHT // 4 + 37)
        )
        text1_rect.x = x
        text2_rect = number_squat.get_rect(
            center=(POPUP_WIDTH // 4, POPUP_HEIGHT // 4 + 75)
        )
        text2_rect.x = x

        settings_surface.blit(time_settings, text1_rect)
        settings_surface.blit(number_squat, text2_rect)

        button1_minus_x = text1_rect.right + BUTTON_MARGIN // 2
        button1_minus_y = text1_rect.centery - BUTTON_HEIGHT // 3 // 2
        button1_minus_rect = pygame.Rect(
            button1_minus_x, button1_minus_y, BUTTON_WIDTH // 3, BUTTON_HEIGHT // 3
        )

        self.time_count_btn_minus = pygame.Rect(
            button1_minus_x + popup_x,
            button1_minus_y + popup_y,
            BUTTON_WIDTH // 3,
            BUTTON_HEIGHT // 3,
        )

        button1_plus_x = text1_rect.right + BUTTON_MARGIN // 2 + BUTTON_WIDTH * 2 // 3
        button1_plus_y = button1_minus_y
        button1_plus_rect = pygame.Rect(
            button1_plus_x, button1_plus_y, BUTTON_WIDTH // 3, BUTTON_HEIGHT // 3
        )
        self.time_count_btn_plus = pygame.Rect(
            button1_plus_x + popup_x,
            button1_plus_y + popup_y,
            BUTTON_WIDTH // 3,
            BUTTON_HEIGHT // 3,
        )

        bold_font_small = pygame.font.Font(
            os.path.join(RESOURCE, "Baloo2-Bold.ttf"), 18
        )

        time_count = bold_font_small.render(f"{self.time_count:02d}", True, (0, 0, 0))
        text_time_rect = time_count.get_rect(
            center=(
                button1_minus_x + BUTTON_WIDTH * 2 // 3,
                button1_plus_y + 18 * 2 // 3,
            )
        )
        text_time_rect.x = button1_minus_x + BUTTON_WIDTH // 3

        # Blit the buttons on the settings_surface
        settings_surface.blit(btn_minus, button1_minus_rect)
        settings_surface.blit(btn_plus, button1_plus_rect)
        settings_surface.blit(time_count, text_time_rect)

        button2_minus_x = text1_rect.right + BUTTON_MARGIN // 2
        button2_minus_y = text2_rect.centery - BUTTON_HEIGHT // 3 // 2
        button2_minus_rect = pygame.Rect(
            button2_minus_x, button2_minus_y, BUTTON_WIDTH // 3, BUTTON_HEIGHT // 3
        )

        self.goal_count_btn_minus = pygame.Rect(
            button2_minus_x + popup_x,
            button2_minus_y + popup_y,
            BUTTON_WIDTH // 3,
            BUTTON_HEIGHT // 3,
        )

        button2_plus_x = text1_rect.right + BUTTON_MARGIN // 2 + BUTTON_WIDTH * 2 // 3
        button2_plus_y = button2_minus_y
        button2_plus_rect = pygame.Rect(
            button2_plus_x, button2_plus_y, BUTTON_WIDTH // 3, BUTTON_HEIGHT // 3
        )
        self.goal_count_btn_plus = pygame.Rect(
            button2_plus_x + popup_x,
            button2_plus_y + popup_y,
            BUTTON_WIDTH // 3,
            BUTTON_HEIGHT // 3,
        )

        number_squat_text = bold_font_small.render(
            f"{self.goal_count:02d}", True, (0, 0, 0)
        )
        text_squat_rect = number_squat_text.get_rect(
            center=(
                button2_minus_x + BUTTON_WIDTH * 2 // 3,
                button2_plus_y + 18 * 2 // 3,
            )
        )
        text_squat_rect.x = button2_minus_x + BUTTON_WIDTH // 3

        settings_surface.blit(number_squat_text, text_squat_rect)
        settings_surface.blit(btn_minus, button2_minus_rect)
        settings_surface.blit(btn_plus, button2_plus_rect)

        # Center the headers inside the popup
        header1_rect = header1.get_rect(center=(POPUP_WIDTH // 4, POPUP_HEIGHT // 4))
        header1_rect.x = x
        header2_rect = header2.get_rect(
            center=(POPUP_WIDTH // 4, POPUP_HEIGHT * 3 // 4)
        )
        header2_rect.x = x
        settings_surface.blit(header1, header1_rect)
        settings_surface.blit(header2, header2_rect)
        button_x = header2_rect.centerx + BUTTON_MARGIN
        button_y = header2_rect.centery - BUTTON_HEIGHT // 2
        button_rect = pygame.Rect(button_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)

        if self.dev_mode_able:
            settings_surface.blit(btn_able_image, button_rect)
        else:
            settings_surface.blit(btn_disable_image, button_rect)

        self.button_rect = pygame.Rect(
            button_x + popup_x, button_y + popup_y, BUTTON_WIDTH, BUTTON_HEIGHT
        )

        self.screen.blit(settings_surface, (popup_x, popup_y))

    def end_game_popup(self):
        # create a blurred background with alpha
        background = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        background.fill((0, 0, 0, 128))
        self.screen.blit(background, (0, 0))

        popup_x = (WINDOW_WIDTH - POPUP_WIDTH) // 2
        popup_y = (WINDOW_HEIGHT - POPUP_HEIGHT) // 2

        
        # load image with popup size
        if not self.is_open_gift:
            if self.current_count == 0 and self.current_clock >= 0:
                win_image = pygame.image.load(os.path.join(RESOURCE, "winning.png"))
                win_image = pygame.transform.scale(win_image, (POPUP_WIDTH, POPUP_HEIGHT))
                self.screen.blit(win_image, (popup_x, popup_y))
                # load open gif btn image, center of button is center bottom of popup
                self.open_btn = pygame.image.load(os.path.join(RESOURCE, "open_gift.png"))
                self.open_btn = pygame.transform.scale(
                    self.open_btn, (POPUP_WIDTH // 2, POPUP_HEIGHT // 6)
                )
                self.open_btn_rect = self.open_btn.get_rect(
                    center=(popup_x + POPUP_WIDTH // 2, popup_y + POPUP_HEIGHT)
                )
                self.screen.blit(self.open_btn, self.open_btn_rect)

            elif self.current_clock < 0:
                lose_image = pygame.image.load(
                    os.path.join(RESOURCE, "time_out_pop_up.png")
                )
                lose_image = pygame.transform.scale(lose_image, (POPUP_WIDTH, POPUP_HEIGHT))
                self.screen.blit(lose_image, (popup_x, popup_y))
                # load replay button image, center of button is center bottom of popup
                self.replay_btn = pygame.image.load(
                    os.path.join(RESOURCE, "replay_button.png")
                )
                self.replay_btn = pygame.transform.scale(
                    self.replay_btn, (POPUP_WIDTH // 2, POPUP_HEIGHT // 6)
                )
                self.replay_btn_rect = self.replay_btn.get_rect(
                    center=(popup_x + POPUP_WIDTH // 2, popup_y + POPUP_HEIGHT)
                )
                self.screen.blit(self.replay_btn, self.replay_btn_rect)
        else:
            popup_y = (WINDOW_HEIGHT - POPUP_HEIGHT * 4 // 3) // 2
            qr_image = pygame.image.load(os.path.join(RESOURCE, "qr_image.png"))
            qr_image = pygame.transform.scale(qr_image, (POPUP_WIDTH, POPUP_HEIGHT * 4 // 3))
            self.screen.blit(qr_image, (popup_x, popup_y))
            #load btn replay image
            self.replay_btn = pygame.image.load(
                os.path.join(RESOURCE, "replay_button.png")
            )
            self.replay_btn = pygame.transform.scale(
                self.replay_btn, (POPUP_WIDTH // 2, POPUP_HEIGHT // 6)
            )
            self.replay_btn_rect = self.replay_btn.get_rect(
                center=(popup_x + POPUP_WIDTH // 2, popup_y + POPUP_HEIGHT * 4 // 3)
            )
            self.screen.blit(self.replay_btn, self.replay_btn_rect)

    def run(self):
        while True:
            self.handle_events()

            ret, self.frame = self.camera.read()
            if not ret:
                continue
            self.frame = cv2.resize(self.frame, (WINDOW_WIDTH, WINDOW_HEIGHT))
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            if not self.is_playing:
                self.process_frame()
                self.display_menu()
            else:
                self.process_frame()
                self.display_game()

            pygame.display.flip()
            fps = self.clock.get_fps()
            # print("FPS: ", fps)
            self.clock.tick(30)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event)

    def handle_mouse_click(self, event):
        if not self.is_playing:
            if not self.show_settings_popup and self.play_button_rect.collidepoint(
                event.pos
            ):
                self.is_playing = True
                self.start_signal = True
                # self.start_signal_time = time.time()
                self.start_time_count = None
                self.current_count = self.goal_count

            elif self.settings_button_rect.collidepoint(event.pos):
                self.show_settings_popup = True
            elif (
                self.show_settings_popup
                and self.button_rect is not None
                and self.button_rect.collidepoint(event.pos)
            ):
                self.dev_mode_able = not self.dev_mode_able
            elif (
                self.show_settings_popup
                and self.time_count_btn_minus is not None
                and self.time_count_btn_minus.collidepoint(event.pos)
            ):
                self.time_count -= 1
                if self.time_count < 0:
                    self.time_count = 0
            elif (
                self.show_settings_popup
                and self.time_count_btn_plus is not None
                and self.time_count_btn_plus.collidepoint(event.pos)
            ):
                self.time_count += 1
            elif (
                self.show_settings_popup
                and self.goal_count_btn_minus is not None
                and self.goal_count_btn_minus.collidepoint(event.pos)
            ):
                self.goal_count -= 1
                if self.goal_count < 0:
                    self.goal_count = 0
            elif (
                self.show_settings_popup
                and self.goal_count_btn_plus is not None
                and self.goal_count_btn_plus.collidepoint(event.pos)
            ):
                self.goal_count += 1
            elif self.show_settings_popup and not self.settings_surface.collidepoint(
                event.pos
            ):
                self.show_settings_popup = False
        else:
            if self.reset_btn_rect.collidepoint(event.pos) or (
                (self.current_count == 0 or self.current_clock < 0)
                and self.replay_btn is not None
                and self.replay_btn_rect.collidepoint(event.pos)
            ):
                self.start_time_count = None
                self.start_signal = False
                self.is_playing = False
                self.is_validated = False
                self.current_clock = 0

            if self.open_btn is not None and self.open_btn_rect.collidepoint(event.pos):
                self.is_open_gift = True
    def process_frame(self):
        if not self.is_playing:
            blurred_frame = cv2.GaussianBlur(self.frame, (BLUR_RADIUS, BLUR_RADIUS), 0)
            self.frame = blurred_frame
        else:
            result = self.pose_landmarker.predict(self.frame)
            pose_landmarks_list = result.pose_landmarks

            if self.dev_mode_able:
                self.frame = PoseLandmarker.draw_landmarks_on_image(self.frame, result)

            if len(pose_landmarks_list) > 0:
                # TODO filter only landmarks in ROI
                pose_landmarks_list = pose_landmarks_list[0]
                list_landmarks = [
                    item for item in pose_landmarks_list if item.visibility > 0.5
                ]
                roi_bb = [ROI_X, ROI_Y, ROI_X + ROI_W, ROI_H + ROI_Y]
                valid_landmarks = []
                for landmark in list_landmarks:
                    point = [landmark.x, landmark.y]
                    point[0] *= self.frame.shape[1]
                    point[1] *= self.frame.shape[0]
                    if PoseLandmarker.is_in_roi(roi_bb, point):
                        valid_landmarks.append(landmark)
                list_landmarks = valid_landmarks

                if len(list_landmarks) >= 23 and not self.is_validated:
                    self.is_validated = True
                    self.start_signal_time = time.time()
                hip_info, knee_info, ankle_info = (
                    pose_landmarks_list[mp.solutions.pose.PoseLandmark.LEFT_HIP.value],
                    pose_landmarks_list[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value],
                    pose_landmarks_list[
                        mp.solutions.pose.PoseLandmark.LEFT_ANKLE.value
                    ],
                )
                # check is hip, knee and ankle scorce in range > 0.5
                if (
                    hip_info.visibility < 0.5
                    or knee_info.visibility < 0.5
                    or ankle_info.visibility < 0.5
                ):
                    return

                hip = (hip_info.x, hip_info.y)
                knee = (knee_info.x, knee_info.y)
                ankle = (ankle_info.x, ankle_info.y)
                angle_knee = PoseLandmarker.calculate_angle(hip, knee, ankle)
                # print(self.current_status, self.current_count)
                if self.current_status == "STANDING" and angle_knee <= 135:
                    self.current_status = "SQUATTING"
                    self.current_count -= 1
                    if self.current_count < 0:
                        self.current_count = 0
                if angle_knee > 170:
                    self.current_status = "STANDING"

    def display_menu(self):
        self.frame = np.rot90(self.frame)
        pygame_frame = pygame.surfarray.make_surface(self.frame)
        self.screen.blit(pygame_frame, (0, 0))

        self.play_button_rect = self.play_button_image.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT * 2 // 3)
        )
        self.settings_button_rect = self.settings_button_image.get_rect(
            topleft=(PADDING // 4, PADDING // 4)
        )

        self.screen.blit(self.play_button_image, self.play_button_rect)
        self.screen.blit(
            self.transparent_image,
            (
                WINDOW_WIDTH // 2 - RULE_WIDTH // 2,
                WINDOW_HEIGHT - RULE_HEIGHT - PADDING,
            ),
        )
        self.screen.blit(self.settings_button_image, (PADDING // 4, PADDING // 4))
        self.screen.blit(
            self.game_name,
            (
                WINDOW_WIDTH // 2 - GAME_NAME_WIDTH // 2,
                WINDOW_HEIGHT // 3 - GAME_NAME_HEIGHT // 2,
            ),
        )

        self.handle_mouse_cursor()

        if self.show_settings_popup:
            self.display_settings_popup()

    def display_game(self):
        self.frame = np.rot90(self.frame)
        pygame_frame = pygame.surfarray.make_surface(self.frame)
        self.screen.blit(pygame_frame, (0, 0))

        # blit reset button
        self.reset_btn_rect = self.reset_btn_image.get_rect(
            topleft=(PADDING // 4, PADDING // 4)
        )
        self.screen.blit(self.reset_btn_image, (PADDING // 4, PADDING // 4))
        self.handle_mouse_cursor()
        self.display_count_down()
        self.display_roi()
        if self.current_clock < 0 or self.current_count == 0:
            self.end_game_popup()

        pygame.display.flip()
        self.clock.tick(30)

    def handle_mouse_cursor(self):
        if (
            (
                not self.show_settings_popup
                and not self.is_playing
                and self.play_button_rect.collidepoint(pygame.mouse.get_pos())
            )
            or (
                self.show_settings_popup
                and (
                    (
                        self.button_rect is not None
                        and self.button_rect.collidepoint(pygame.mouse.get_pos())
                    )
                    or (
                        self.time_count_btn_minus is not None
                        and self.time_count_btn_minus.collidepoint(
                            pygame.mouse.get_pos()
                        )
                    )
                    or (
                        self.time_count_btn_plus is not None
                        and self.time_count_btn_plus.collidepoint(
                            pygame.mouse.get_pos()
                        )
                    )
                    or (
                        self.goal_count_btn_minus is not None
                        and self.goal_count_btn_minus.collidepoint(
                            pygame.mouse.get_pos()
                        )
                    )
                    or (
                        self.goal_count_btn_plus is not None
                        and self.goal_count_btn_plus.collidepoint(
                            pygame.mouse.get_pos()
                        )
                    )
                )
            )
            or (
                self.is_playing
                and (
                    self.reset_btn_rect.collidepoint(pygame.mouse.get_pos())
                    or (
                        (self.current_count == 0 or self.current_clock < 0)
                        and (
                            (
                                self.replay_btn is not None
                                and self.replay_btn_rect.collidepoint(
                                    pygame.mouse.get_pos()
                                )
                            )
                            or (
                                self.open_btn is not None
                                and self.open_btn_rect.collidepoint(
                                    pygame.mouse.get_pos()
                                )
                            )
                        )
                    )
                )
            )
            or (
                not self.is_playing
                and self.settings_button_rect.collidepoint(pygame.mouse.get_pos())
            )
        ):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)


if __name__ == "__main__":
    game = Game()
    game.run()
