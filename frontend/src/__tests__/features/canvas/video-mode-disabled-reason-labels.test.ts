import { describe, expect, it } from "vitest";

import { videoModeDisabledReason } from "@/features/canvas/nodes/shared/VideoGenerationForm";
import { enT } from "../../helpers/i18n-fixtures";

const NONE = { videos: 0, images: 0, audios: 0 };
const WITHOUT_VIDEO_EDIT = ["text_to_video", "first_frame", "first_last_frame", "all_reference", "image_reference"];
const WITH_VIDEO_EDIT = [...WITHOUT_VIDEO_EDIT, "video_edit"];

// Hover reasons must quote the visible tab names (node.videoNode.tabs.*), not other wording.
describe("shared videoModeDisabledReason quotes the visible tab labels", () => {
  it("HappyHorse: a connected video points at the Video Edit tab", () => {
    expect(videoModeDisabledReason("textToVideo", "happyhorse-1.0", { ...NONE, videos: 1 }, enT)).toBe(
      'A video node is connected. Use "Video Edit"',
    );
  });

  it("HappyHorse: a connected image points at the First Frame / Image Reference tabs", () => {
    expect(videoModeDisabledReason("textToVideo", "happyhorse-1.0", { ...NONE, images: 1 }, enT)).toBe(
      'An image node is connected. Pick "First Frame" or "Image Reference"',
    );
  });

  it("models without video_edit name the Video Edit tab", () => {
    expect(
      videoModeDisabledReason("videoEdit", "seedance-2.0", { ...NONE, videos: 1 }, enT, WITHOUT_VIDEO_EDIT),
    ).toBe('This model doesn\'t support "Video Edit"');
  });

  it("upstream video restricts to the All Reference / Video Edit tabs", () => {
    expect(
      videoModeDisabledReason("firstFrame", "seedance-2.0", { ...NONE, videos: 1 }, enT, WITH_VIDEO_EDIT),
    ).toBe('With video upstream, only "All Reference" or "Video Edit" are available');
    expect(
      videoModeDisabledReason("firstFrame", "seedance-2.0", { ...NONE, videos: 1 }, enT, WITHOUT_VIDEO_EDIT),
    ).toBe('With video upstream, only "All Reference" is available');
  });
});
