//
//  Item.swift
//  App Name
//
//  Created by Ansh Nanda on 3/25/26.
//

import Foundation
import SwiftData

@Model
final class Item {
    var timestamp: Date
    
    init(timestamp: Date) {
        self.timestamp = timestamp
    }
}
