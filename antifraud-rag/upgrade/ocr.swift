import Foundation
import Vision
import AppKit
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["en-US", "zh-Hans"]
try VNImageRequestHandler(url: url).perform([request])
let rows = (request.results ?? []).compactMap { result -> [String: Any]? in
    guard let text = result.topCandidates(1).first else { return nil }
    let b = result.boundingBox
    return ["text": text.string, "confidence": text.confidence, "region_normalized_bottom_left": [b.origin.x,b.origin.y,b.size.width,b.size.height]]
}
let data = try JSONSerialization.data(withJSONObject: rows, options: [])
print(String(data: data, encoding: .utf8)!)
