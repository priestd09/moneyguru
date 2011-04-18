/* 
Copyright 2011 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "BSD" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/bsd_license
*/

#import <Cocoa/Cocoa.h>
#import "PyPanel.h"

@interface PyBudgetPanel : PyPanel {}
- (NSString *)startDate;
- (void)setStartDate:(NSString *)startDate;
- (NSString *)stopDate;
- (void)setStopDate:(NSString *)stopDate;
- (NSInteger)repeatEvery;
- (void)setRepeatEvery:(NSInteger)value;
- (NSString *)repeatEveryDesc;
- (NSInteger)repeatTypeIndex;
- (void)setRepeatTypeIndex:(NSInteger)value;
- (NSArray *)repeatOptions;
- (NSInteger)accountIndex;
- (void)setAccountIndex:(NSInteger)index;
- (NSInteger)targetIndex;
- (void)setTargetIndex:(NSInteger)index;
- (NSString *)amount;
- (void)setAmount:(NSString *)amount;
- (NSString *)notes;
- (void)setNotes:(NSString *)notes;

- (NSArray *)accountOptions;
- (NSArray *)targetOptions;
@end