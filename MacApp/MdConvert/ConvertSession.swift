import AppKit
import Foundation
import Observation
import UniformTypeIdentifiers

@MainActor
@Observable
final class ConvertSession {
    var items: [QueueItem] = []
    var isBusy = false
    var isDropTargeted = false
    var footer: FooterKind = .ready

    var queuedCount: Int {
        items.filter { $0.status == .queued }.count
    }

    var canConvert: Bool {
        !isBusy && queuedCount > 0
    }

    var canClear: Bool {
        !isBusy && !items.isEmpty
    }

    func add(urls: [URL], startConvert: Bool, settings: SettingsStore) {
        var changed = false
        for url in urls {
            var resolved = url
            if url.isFileURL {
                resolved = url.standardizedFileURL
            }
            var isDir: ObjCBool = false
            guard FileManager.default.fileExists(atPath: resolved.path, isDirectory: &isDir), !isDir.boolValue else {
                continue
            }
            if !AllowedTypes.isAllowed(url: resolved) {
                continue
            }
            if let index = items.firstIndex(where: { $0.id == resolved.path }) {
                if items[index].status == .done || failed(items[index]) {
                    items[index].status = .queued
                    changed = true
                }
                continue
            }
            items.append(QueueItem(url: resolved))
            changed = true
        }
        if startConvert && queuedCount > 0 {
            Task { await convertQueued(using: settings) }
            return
        }
        if changed && !isBusy {
            footer = .queued(queuedCount)
        }
    }

    func clear() {
        guard canClear else { return }
        items.removeAll()
        footer = .ready
    }

    func convertQueued(using settings: SettingsStore, newRun: Bool = true) async {
        if isBusy { return }
        let pendingIDs = items.filter { $0.status == .queued }.map(\.id)
        if pendingIDs.isEmpty { return }

        isBusy = true
        var ok = newRun ? 0 : items.filter { $0.status == .done }.count
        var failedCount = newRun ? 0 : items.filter { if case .failed = $0.status { return true }; return false }.count
        let already = ok + failedCount
        let total = already + pendingIDs.count
        let config = settings.snapshot

        for (offset, id) in pendingIDs.enumerated() {
            guard let index = items.firstIndex(where: { $0.id == id }) else { continue }
            items[index].status = .converting
            footer = .converting(current: already + offset + 1, total: total)
            let url = items[index].url
            let result = await CLIRunner.convert(file: url, config: config)
            guard let latest = items.firstIndex(where: { $0.id == id }) else { continue }
            if result.ok {
                items[latest].status = .done
                ok += 1
            } else {
                items[latest].status = .failed(result.message)
                failedCount += 1
            }
        }

        isBusy = false
        footer = .finished(ok: ok, failed: failedCount)

        if queuedCount > 0 {
            await convertQueued(using: settings, newRun: false)
        }
    }

    func chooseFiles(settings: SettingsStore) {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = true
        panel.canCreateDirectories = false
        panel.prompt = "Add"
        panel.message = "Select files to convert"
        panel.allowedContentTypes = AllowedTypes.contentTypes
        panel.allowsOtherFileTypes = false
        guard panel.runModal() == .OK else { return }
        add(urls: panel.urls, startConvert: false, settings: settings)
    }

    func ingestDropProviders(_ providers: [NSItemProvider], settings: SettingsStore) {
        Task {
            let urls = await Self.loadFileURLs(from: providers)
            add(urls: urls, startConvert: true, settings: settings)
        }
    }

    private func failed(_ item: QueueItem) -> Bool {
        if case .failed = item.status { return true }
        return false
    }

    private static func loadFileURLs(from providers: [NSItemProvider]) async -> [URL] {
        var urls: [URL] = []
        for provider in providers {
            guard provider.hasItemConformingToTypeIdentifier(UTType.fileURL.identifier) else { continue }
            let url: URL? = await withCheckedContinuation { continuation in
                provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, _ in
                    continuation.resume(returning: Self.url(from: item))
                }
            }
            if let url {
                urls.append(url)
            }
        }
        return urls
    }

    private static func url(from item: NSSecureCoding?) -> URL? {
        if let url = item as? URL {
            return url
        }
        if let data = item as? Data {
            return URL(dataRepresentation: data, relativeTo: nil)
        }
        if let string = item as? String {
            if let url = URL(string: string), url.isFileURL {
                return url
            }
            return URL(fileURLWithPath: string)
        }
        return nil
    }
}
