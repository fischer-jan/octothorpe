import SwiftUI

struct FileRowView: View {
    var item: QueueItem

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: AllowedTypes.symbolName(for: item.url))
                .font(.title3)
                .foregroundStyle(.secondary)
                .frame(width: 24)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 2) {
                Text(item.filename)
                    .font(.body)
                    .foregroundStyle(.primary)
                    .lineLimit(1)
                Text(item.folder)
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                    .truncationMode(.middle)
                if case .failed(let message) = item.status {
                    Text(message)
                        .font(.caption)
                        .foregroundStyle(.red)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            statusView
        }
        .padding(.vertical, 4)
        .accessibilityElement(children: .combine)
    }

    @ViewBuilder
    private var statusView: some View {
        switch item.status {
        case .queued:
            Text("Queued")
                .font(.callout)
                .foregroundStyle(.secondary)
        case .converting:
            HStack(spacing: 6) {
                ProgressView()
                    .controlSize(.small)
                Text("Converting…")
                    .font(.callout)
                    .foregroundStyle(.tint)
            }
        case .done:
            Label("Done", systemImage: "checkmark.circle.fill")
                .font(.callout)
                .foregroundStyle(.green)
                .labelStyle(.titleAndIcon)
        case .failed:
            Label("Failed", systemImage: "xmark.circle.fill")
                .font(.callout)
                .foregroundStyle(.red)
                .labelStyle(.titleAndIcon)
        }
    }
}
