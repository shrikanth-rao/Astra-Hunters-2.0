
import cv2


def main():
    # Open the default laptop webcam
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not access the webcam.")
        print("Check Windows camera permissions and try again.")
        return

    print("Webcam connected successfully!")
    print("Press Q to close the camera window.")

    while True:
        success, frame = camera.read()

        if not success:
            print("ERROR: Could not read a frame.")
            break

        # Mirror the video for a natural webcam preview
        frame = cv2.flip(frame, 1)

        # Display a status message
        cv2.putText(
            frame,
            "Webcam Test - Press Q to quit",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Speaker Analysis - Webcam Test", frame)

        # Quit when Q is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
