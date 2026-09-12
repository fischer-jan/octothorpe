import SwiftUI
import UniformTypeIdentifiers

struct DropZoneView: View {
    var hasFiles: Bool
    @Binding var isTargeted: Bool
    var onTap: () -> Void
    var onDropProviders: ([NSItemProvider]) -> Void

    var body: some View {
        Button(action: onTap) {
            ZStack {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(isTargeted ? Color.accentColor.opacity(0.12) : Color.clear)
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .strokeBorder(
                        isTargeted ? Color.accentColor : Color.secondary.opacity(0.45),
                        style: StrokeStyle(lineWidth: 1.5, dash: [7, 5])
                    )
                VStack(spacing: 4) {
                    Text("Drop files to convert")
                        .font(hasFiles ? .body : .title3)
                        .foregroundStyle(hasFiles ? .secondary : .primary)
                    if hasFiles {
                        Text("Drop starts convert")
                            .font(.callout)
                            .foregroundStyle(.tertiary)
                    } else {
                        Text("PDF, Office, images, HTML, text, and more")
                            .font(.callout)
                            .foregroundStyle(.tertiary)
                            .multilineTextAlignment(.center)
                    }
                }
                .padding(.horizontal, 16)
            }
            .frame(maxWidth: .infinity)
            .frame(minHeight: hasFiles ? 56 : 160, maxHeight: hasFiles ? 72 : .infinity)
            .contentShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Add files")
        .accessibilityHint("Opens a file picker. Dropped files start convert.")
        .onDrop(of: [.fileURL], isTargeted: $isTargeted) { providers in
            onDropProviders(providers)
            return true
        }
    }
}
