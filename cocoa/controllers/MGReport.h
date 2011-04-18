/* 
Copyright 2011 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "BSD" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/bsd_license
*/

#import <Cocoa/Cocoa.h>
#import "HSOutline.h"
#import "PyReport.h"
#import "MGColumns.h"

@interface MGReport : HSOutline {
    MGColumns *columns;
    BOOL toggleExcludedIsEnabled;
}
- (PyReport *)py;

- (IBAction)showSelectedAccount:(id)sender;
- (BOOL)canShowSelectedAccount;
- (MGColumns *)columns;
@end
