import SwiftUI

struct FooterBar: View {
    var footer: FooterKind

    var body: some View {
        HStack {
            Text(footer.text)
                .font(.callout)
                .foregroundStyle(color)
                .lineLimit(2)
            Spacer(minLength: 0)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(footer.text)
    }

    private var color: Color {
        switch footer {
        case .ready, .queued:
            return .secondary
        case .converting:
            return .accentColor
        case .finished(_, let failed):
            return failed > 0 ? .red : .green
        case .error:
            return .red
        }
    }
}
